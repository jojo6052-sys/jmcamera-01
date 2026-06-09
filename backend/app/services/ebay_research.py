from __future__ import annotations

import base64
import random
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, quote, unquote, urlparse
from uuid import uuid4

import requests
from bs4 import BeautifulSoup

from app.config import settings

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
    "Cache-Control": "no-cache",
}
EBAY_SEARCH_URL = "https://www.ebay.com/sch/i.html"
EBAY_OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"
EBAY_BLOCKED_MESSAGE = (
    "eBay blocked this server-side request with HTTP 403 Forbidden. "
    "The seller URL is valid, but eBay is refusing automated access from this environment; "
    "try again later or use an official eBay API/import flow for reliable production collection."
)


class EbayFetchBlockedError(RuntimeError):
    """Raised when eBay refuses direct server-side page fetching."""


@dataclass
class CompetitorItemPayload:
    external_item_id: str
    title: str
    normalized_title: str
    item_url: str
    image_url: str | None
    price: Decimal | None
    currency: str | None
    item_status: str
    source_url: str
    raw: dict


def extract_ebay_seller_username(seller_url: str) -> str:
    parsed = urlparse(seller_url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("seller_url must be a full eBay seller URL")
    host = parsed.netloc.lower()
    if "ebay." not in host:
        raise ValueError("seller_url must be an eBay URL")

    query_seller = parse_qs(parsed.query).get("_ssn")
    if query_seller and query_seller[0].strip():
        return query_seller[0].strip()

    parts = [unquote(part) for part in parsed.path.split("/") if part]
    for marker in ("str", "usr"):
        if marker in parts:
            idx = parts.index(marker)
            if idx + 1 < len(parts) and parts[idx + 1].strip():
                return parts[idx + 1].strip()

    if len(parts) == 1 and parts[0].strip():
        return parts[0].strip()

    raise ValueError("could not extract eBay seller username from URL")


def build_ebay_seller_search_url(seller_username: str, item_status: str) -> str:
    status_params = "&LH_Sold=1&LH_Complete=1" if item_status == "sold" else ""
    return f"{EBAY_SEARCH_URL}?_ssn={quote(seller_username)}{status_params}&_sop=13"


def fetch_competitor_items(seller_url: str, *, include_active: bool = True, include_sold: bool = True, limit: int = 50) -> tuple[str, list[CompetitorItemPayload]]:
    seller_username = extract_ebay_seller_username(seller_url)
    capped_limit = max(1, min(limit, 100))
    rows: list[CompetitorItemPayload] = []

    if include_active and has_ebay_api_credentials():
        rows.extend(fetch_active_items_with_browse_api(seller_username, limit=capped_limit))
        include_active = False

    if (include_active or include_sold) and _public_fetch_enabled():
        for item_status in _requested_statuses(include_active=include_active, include_sold=include_sold):
            source_url = build_ebay_seller_search_url(seller_username, item_status)
            _polite_public_wait()
            html = _fetch_html(source_url)
            rows.extend(_parse_ebay_items(html, source_url=source_url, item_status=item_status, limit=capped_limit))

    return seller_username, rows[:capped_limit]


def has_ebay_api_credentials() -> bool:
    return bool(settings.ebay_client_id.strip() and settings.ebay_client_secret.strip())


def _public_fetch_enabled() -> bool:
    return settings.ebay_public_fetch_mode.strip().lower() == "live"


def _polite_public_wait() -> None:
    min_delay = max(0.0, settings.ebay_public_request_min_delay_seconds)
    max_delay = max(min_delay, settings.ebay_public_request_max_delay_seconds)
    time.sleep(random.uniform(min_delay, max_delay))


def fetch_active_items_with_browse_api(seller_username: str, *, limit: int) -> list[CompetitorItemPayload]:
    token = get_ebay_application_token()
    params = {
        "filter": f"sellers:{{{seller_username}}}",
        "limit": max(1, min(limit, 100)),
    }
    response = requests.get(
        EBAY_BROWSE_SEARCH_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": settings.ebay_marketplace_id,
            "Accept": "application/json",
        },
        params=params,
        timeout=12,
    )
    response.raise_for_status()
    return _parse_browse_api_items(response.json(), source_url=response.url, limit=limit)


def get_ebay_application_token() -> str:
    client_id = settings.ebay_client_id.strip()
    client_secret = settings.ebay_client_secret.strip()
    if not client_id or not client_secret:
        raise ValueError("eBay API credentials are not configured")

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    response = requests.post(
        EBAY_OAUTH_TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": EBAY_OAUTH_SCOPE,
        },
        timeout=12,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise ValueError("eBay OAuth response did not include access_token")
    return token


def _parse_browse_api_items(payload: dict, *, source_url: str, limit: int) -> list[CompetitorItemPayload]:
    rows: list[CompetitorItemPayload] = []
    for item in payload.get("itemSummaries", [])[:limit]:
        title = item.get("title") or "Untitled eBay item"
        price = item.get("price") or {}
        image = item.get("image") or {}
        rows.append(
            CompetitorItemPayload(
                external_item_id=item.get("itemId") or f"browse-{uuid4().hex[:12]}",
                title=title,
                normalized_title=_normalize_title(title),
                item_url=item.get("itemWebUrl") or item.get("itemHref") or source_url,
                image_url=image.get("imageUrl"),
                price=_decimal_or_none(price.get("value")),
                currency=price.get("currency"),
                item_status="active",
                source_url=source_url,
                raw={"browse_api": item},
            )
        )
    return rows


def _requested_statuses(*, include_active: bool, include_sold: bool) -> list[str]:
    statuses: list[str] = []
    if include_active:
        statuses.append("active")
    if include_sold:
        statuses.append("sold")
    if not statuses:
        raise ValueError("at least one of include_active or include_sold must be true")
    return statuses


def _fetch_html(url: str) -> str:
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=settings.ebay_public_request_timeout_seconds)
    if response.status_code == 403:
        raise EbayFetchBlockedError(EBAY_BLOCKED_MESSAGE)
    response.raise_for_status()
    return response.text


def _parse_ebay_items(html: str, *, source_url: str, item_status: str, limit: int) -> list[CompetitorItemPayload]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("li.s-item")
    rows: list[CompetitorItemPayload] = []

    for card in cards:
        title_el = card.select_one(".s-item__title")
        link_el = card.select_one("a.s-item__link")
        if not title_el or not link_el:
            continue

        title = title_el.get_text(" ", strip=True)
        item_url = link_el.get("href", "").strip()
        if not title or title.lower() == "shop on ebay" or not item_url:
            continue

        price_text = _first_text(card, [".s-item__price", ".ITALIC", ".s-item__detail"])
        image_el = card.select_one(".s-item__image-wrapper img, img.s-item__image-img, img")
        image_url = None
        if image_el:
            image_url = image_el.get("src") or image_el.get("data-src")

        external_id = _extract_item_id(item_url) or f"parsed-{uuid4().hex[:12]}"
        price, currency = _parse_price(price_text)
        rows.append(
            CompetitorItemPayload(
                external_item_id=external_id,
                title=title,
                normalized_title=_normalize_title(title),
                item_url=item_url,
                image_url=image_url,
                price=price,
                currency=currency,
                item_status=item_status,
                source_url=source_url,
                raw={"price_text": price_text},
            )
        )
        if len(rows) >= limit:
            break

    return rows


def _first_text(card, selectors: list[str]) -> str | None:
    for selector in selectors:
        el = card.select_one(selector)
        if el:
            text = el.get_text(" ", strip=True)
            if text:
                return text
    return None


def _extract_item_id(url: str) -> str | None:
    parsed = urlparse(url)
    match = re.search(r"/(?:itm|p)/(?:[^/]+/)?(\d{8,})", parsed.path)
    if match:
        return match.group(1)
    query_item = parse_qs(parsed.query).get("item")
    if query_item and query_item[0].strip():
        return query_item[0].strip()
    return None


def _parse_price(raw: str | None) -> tuple[Decimal | None, str | None]:
    if not raw:
        return None, None
    currency = "USD" if "$" in raw or "US" in raw.upper() else None
    match = re.search(r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)", raw.replace(" ", ""))
    if not match:
        return None, currency
    try:
        return Decimal(match.group(1).replace(",", "")), currency
    except InvalidOperation:
        return None, currency


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def _decimal_or_none(raw: str | int | float | None) -> Decimal | None:
    if raw is None:
        return None
    try:
        return Decimal(str(raw))
    except InvalidOperation:
        return None
