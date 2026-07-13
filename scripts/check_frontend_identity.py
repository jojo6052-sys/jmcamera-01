#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request

SOURCING_MARKERS = (
    "JM Camera Sourcing AI",
    '<div id="root"',
)
LANDING_MARKERS = (
    "Tokyo Serene Days",
    "時間を取り戻す旅へ。",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether a URL is serving the JM Camera sourcing system or the static landing page."
    )
    parser.add_argument("--url", default="http://localhost:5173/", help="URL to inspect. Defaults to http://localhost:5173/")
    parser.add_argument(
        "--expect",
        choices=("sourcing", "landing"),
        default="sourcing",
        help="Expected frontend identity. Defaults to sourcing.",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout seconds. Defaults to 5")
    args = parser.parse_args()

    ok, detail, body = fetch_text(args.url, timeout=args.timeout)
    if not ok:
        print(f"FAIL: could not fetch {args.url}: {detail}")
        return 1

    identity = detect_identity(body)
    if identity == args.expect:
        print(f"PASS: {args.url} is serving {identity} ({detail})")
        return 0

    print(f"FAIL: {args.url} is serving {identity}, expected {args.expect} ({detail})")
    print("Hint: if 5173 shows landing, stop the other landing project/container and rebuild this stack.")
    return 1


def fetch_text(url: str, *, timeout: float) -> tuple[bool, str, str]:
    request = urllib.request.Request(url, method="GET", headers={"Accept": "text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = getattr(response, "status", None)
            if status is None:
                return True, "local file", body
            if 200 <= status < 300:
                return True, f"HTTP {status}", body
            return False, f"HTTP {status}; expected 2xx", body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, f"HTTP {exc.code}; expected 2xx", body
    except urllib.error.URLError as exc:
        return False, f"connection error: {exc.reason}", ""
    except TimeoutError:
        return False, "timeout", ""


def detect_identity(body: str) -> str:
    normalized = body.lower()
    sourcing_score = sum(marker.lower() in normalized for marker in SOURCING_MARKERS)
    landing_score = sum(marker.lower() in normalized for marker in LANDING_MARKERS)

    if landing_score and landing_score >= sourcing_score:
        return "landing"
    if sourcing_score:
        return "sourcing"
    return "unknown"


if __name__ == "__main__":
    sys.exit(main())
