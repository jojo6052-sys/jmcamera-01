from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable


def _as_float(value: Any, default: float = 0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _candidate_text(candidate: Any, field: str) -> str:
    value = getattr(candidate, field, None)
    return str(value or "").lower()


def _rule_matches(candidate: Any, rule: Any) -> bool:
    pattern = str(getattr(rule, "pattern", "") or "").strip().lower()
    if not pattern:
        return False

    match_type = getattr(rule, "match_type", "keyword")
    if match_type == "seller_id":
        return pattern == _candidate_text(candidate, "seller_id")
    if match_type == "description":
        return pattern in _candidate_text(candidate, "description")
    return pattern in f"{_candidate_text(candidate, 'title')} {_candidate_text(candidate, 'normalized_title')} {_candidate_text(candidate, 'search_keyword')}"


def _description_risk_score(description: str) -> tuple[float, list[str]]:
    risk_weights = {
        "返品不可": 1.5,
        "ノークレーム": 2.0,
        "不動": 4.0,
        "部品取り": 4.0,
        "カビ": 2.5,
        "曇り大": 3.0,
        "水没": 5.0,
        "落下": 4.0,
        "ジャンク": 4.0,
        "動作未確認": 3.0,
    }
    hits = [word for word in risk_weights if word in description]
    score = min(15, sum(risk_weights[word] for word in hits))
    return score, hits


def _description_positive_score(description: str) -> tuple[float, list[str]]:
    positive_words = ["動作品", "美品", "防湿庫", "整備済", "確認済", "返品可", "付属品完備"]
    hits = [word for word in positive_words if word in description]
    return min(6, len(hits) * 1.5), hits


def _image_quality_score(image_urls: list[str]) -> tuple[float, float, list[str]]:
    image_count = len(image_urls)
    score = 6 if image_count >= 5 else 5 if image_count >= 3 else 3 if image_count == 2 else 1 if image_count == 1 else 0
    risk = max(0, 6 - score)
    findings: list[str] = []
    if image_count == 0:
        findings.append("写真なし")
    elif image_count < 3:
        findings.append("写真枚数少")

    low_quality_markers = ("blur", "noimage", "placeholder", "missing")
    if any(any(marker in url.lower() for marker in low_quality_markers) for url in image_urls):
        risk += 2
        findings.append("低品質写真の可能性")

    return score, min(10, risk), findings


def _rank(total: float, seller_rating: float, description_risk: float) -> tuple[str, str]:
    if seller_rating < 40:
        return "NG", "Seller rating is too low."
    if description_risk >= 12:
        return "NG", "Description contains critical risk words."
    if total >= 85:
        return "S", ""
    if total >= 70:
        return "A", ""
    if total >= 55:
        return "B", "Check item details before bidding."
    if total >= 40:
        return "C", "Higher risk profile."
    return "NG", "Low expected return and/or high risk."


def compute_recommendation(candidate: Any, scoring_rules: Iterable[Any] | None = None) -> dict:
    current_price = _as_float(getattr(candidate, "current_price_jpy", None))
    buyout_price = _as_float(getattr(candidate, "buyout_price_jpy", None))
    seller_rating = _as_float(getattr(candidate, "seller_rating", None), 70)
    image_urls = list(getattr(candidate, "image_urls", None) or [])
    description = _candidate_text(candidate, "description")

    expected_sale_price_jpy = max(current_price * 1.8, buyout_price * 1.4, 12000)
    expected_sale_price_usd = expected_sale_price_jpy / 155.0
    expected_profit = expected_sale_price_jpy - current_price
    expected_margin = (expected_profit / expected_sale_price_jpy * 100) if expected_sale_price_jpy else 0

    similarity_score = min(25, max(8, 15 + (len(getattr(candidate, "title", None) or "") % 10)))
    profit_score = min(20, max(0, expected_margin / 2.5))
    rotation_score = 10
    seller_score = min(15, max(0, (seller_rating - 70) / 2))

    description_risk, risk_hits = _description_risk_score(description)
    positive_description_score, positive_hits = _description_positive_score(description)
    image_score, image_risk, image_findings = _image_quality_score(image_urls)
    bargain_score = min(10, max(0, (expected_sale_price_jpy - current_price) / 3000))

    matched_rule_reasons: list[str] = []
    manual_score_adjustment = 0.0
    max_bid_adjustment_pct = 0.0
    critical_rule_matched = False
    for rule in scoring_rules or []:
        if not getattr(rule, "enabled", True) or not _rule_matches(candidate, rule):
            continue
        score_delta = _as_float(getattr(rule, "score_adjustment", None))
        bid_delta = _as_float(getattr(rule, "max_bid_adjustment_pct", None))
        manual_score_adjustment += score_delta
        max_bid_adjustment_pct += bid_delta
        risk_level = getattr(rule, "risk_level", "info")
        critical_rule_matched = critical_rule_matched or risk_level == "critical"
        reason = getattr(rule, "reason", None) or getattr(rule, "name", "manual rule")
        matched_rule_reasons.append(f"{getattr(rule, 'name', 'manual rule')}: {reason} ({score_delta:+.1f}pt, bid {bid_delta:+.1f}%)")

    total = (
        similarity_score
        + profit_score
        + rotation_score
        + seller_score
        + (15 - description_risk)
        + positive_description_score
        + bargain_score
        + image_score
        + manual_score_adjustment
    )
    total = max(0, min(100, round(total, 2)))

    rank, caution = _rank(total, seller_rating, description_risk)
    if critical_rule_matched:
        rank = "NG"
        caution = "Manual critical scoring rule matched."
    elif matched_rule_reasons and not caution:
        caution = "Manual knowledge adjustments were applied."

    recommended_max_bid_jpy = current_price * 1.1 * (1 + max_bid_adjustment_pct / 100)

    reason_parts = [
        f"Profit margin {expected_margin:.1f}%",
        f"seller rating {seller_rating:.1f}",
    ]
    if risk_hits:
        reason_parts.append(f"description risks: {', '.join(risk_hits)}")
    if positive_hits:
        reason_parts.append(f"positive description: {', '.join(positive_hits)}")
    if image_findings:
        reason_parts.append(f"image findings: {', '.join(image_findings)}")
    if matched_rule_reasons:
        reason_parts.append("manual knowledge: " + " | ".join(matched_rule_reasons))

    return {
        "similarity_score": round(similarity_score, 2),
        "expected_sale_price_usd": round(expected_sale_price_usd, 2),
        "expected_sale_price_jpy": round(expected_sale_price_jpy, 2),
        "expected_profit_jpy": round(expected_profit, 2),
        "expected_profit_margin": round(expected_margin, 2),
        "recommended_max_bid_jpy": round(max(0, recommended_max_bid_jpy), 2),
        "seller_risk_score": round(max(0, 15 - seller_score), 2),
        "description_risk_score": round(description_risk, 2),
        "image_risk_score": round(image_risk, 2),
        "total_score": total,
        "rank": rank,
        "reason": "; ".join(reason_parts) + ".",
        "caution": caution,
    }
