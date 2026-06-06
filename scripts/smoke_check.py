#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Check:
    name: str
    method: str
    path: str
    expected_status: int = 200


READ_ONLY_CHECKS = [
    Check(name="backend health", method="GET", path="/health"),
    Check(name="api health", method="GET", path="/api/health"),
    Check(name="phase status", method="GET", path="/api/phase/status"),
    Check(name="search keywords list", method="GET", path="/api/search-keywords"),
    Check(name="candidates list", method="GET", path="/api/candidates"),
    Check(name="competitors list", method="GET", path="/api/competitors"),
    Check(name="analytics best sellers", method="GET", path="/api/analytics/best-sellers"),
    Check(name="analytics categories", method="GET", path="/api/analytics/categories"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only smoke checks against a running JM Camera backend.")
    parser.add_argument("--base-url", default="http://localhost:8001", help="Backend base URL. Defaults to http://localhost:8001")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout seconds. Defaults to 5")
    parser.add_argument("--include-write-checks", action="store_true", help="Also create a temporary keyword, fetch Yahoo candidates, and score them.")
    args = parser.parse_args()

    failed = False
    base_url = args.base_url.rstrip("/")
    for check in READ_ONLY_CHECKS:
        ok, detail = run_check(base_url=base_url, check=check, timeout=args.timeout)
        marker = "PASS" if ok else "FAIL"
        print(f"[{marker}] {check.name}: {detail}")
        failed = failed or not ok

    if args.include_write_checks:
        ok, detail = run_write_checks(base_url=base_url, timeout=args.timeout)
        marker = "PASS" if ok else "FAIL"
        print(f"[{marker}] write flow: {detail}")
        failed = failed or not ok

    return 1 if failed else 0


def run_check(*, base_url: str, check: Check, timeout: float) -> tuple[bool, str]:
    request = urllib.request.Request(f"{base_url}{check.path}", method=check.method, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}; expected {check.expected_status}"
    except urllib.error.URLError as exc:
        return False, f"connection error: {exc.reason}"
    except TimeoutError:
        return False, "timeout"

    if status != check.expected_status:
        return False, f"HTTP {status}; expected {check.expected_status}"

    parsed = parse_json(body)
    if check.path == "/api/phase/status" and isinstance(parsed, dict):
        database = parsed.get("database")
        ready_checks = parsed.get("ready_checks")
        if database != "ok" or not isinstance(ready_checks, dict) or not ready_checks.get("database_connected"):
            return False, "phase status did not report database_connected"
    return True, f"HTTP {status}"


def run_write_checks(*, base_url: str, timeout: float) -> tuple[bool, str]:
    keyword = f"smoke canon eos {int(time.time())}"
    keyword_payload = {
        "keyword": keyword,
        "category": "Smoke Check",
        "brand": "Canon",
        "priority": 999,
        "active": True,
    }
    keyword_ok, keyword_response = request_json(
        base_url=base_url,
        method="POST",
        path="/api/search-keywords",
        payload=keyword_payload,
        timeout=timeout,
    )
    if not keyword_ok:
        return False, f"failed to create search keyword: {keyword_response}"

    yahoo_ok, yahoo_response = request_json(
        base_url=base_url,
        method="POST",
        path="/api/yahoo/search",
        payload={"keyword": keyword, "limit": 2},
        timeout=timeout,
    )
    if not yahoo_ok or not isinstance(yahoo_response, list) or not yahoo_response:
        return False, f"failed to fetch yahoo candidates: {yahoo_response}"

    candidate_ids = [item.get("id") for item in yahoo_response if isinstance(item, dict) and item.get("id")]
    if not candidate_ids:
        return False, "yahoo search returned no candidate ids"

    score_ok, score_response = request_json(
        base_url=base_url,
        method="POST",
        path="/api/candidates/score-batch",
        payload={"candidate_ids": candidate_ids},
        timeout=timeout,
    )
    if not score_ok or not isinstance(score_response, list) or len(score_response) != len(candidate_ids):
        return False, f"failed to score candidates: {score_response}"

    return True, f"created keyword '{keyword}', fetched {len(candidate_ids)} candidates, scored {len(score_response)} candidates"


def request_json(*, base_url: str, method: str, path: str, payload: dict, timeout: float) -> tuple[bool, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        method=method,
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            return 200 <= response.status < 300, parse_json(response_body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        return False, {"status": exc.code, "body": parse_json(error_body) or error_body}
    except urllib.error.URLError as exc:
        return False, f"connection error: {exc.reason}"
    except TimeoutError:
        return False, "timeout"


def parse_json(body: str) -> Any:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


if __name__ == "__main__":
    sys.exit(main())
