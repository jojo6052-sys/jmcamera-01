#!/usr/bin/env python3
"""Check that localhost:5173 serves JM Camera Sourcing AI, not another project."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request

EXPECTED_MARKERS = ("JM Camera Sourcing AI", 'id="root"')
LANDING_HINTS = ("landing", "Landing", "LP", "ランディング")


def fetch(url: str, timeout: float) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the sourcing frontend identity on port 5173.")
    parser.add_argument("--url", default="http://localhost:5173/", help="Frontend URL to check. Defaults to http://localhost:5173/")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    try:
        body = fetch(args.url, args.timeout)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Failed to fetch {args.url}: {exc}", file=sys.stderr)
        return 1

    missing = [marker for marker in EXPECTED_MARKERS if marker not in body]
    if missing:
        landing_hint = any(hint in body for hint in LANDING_HINTS)
        hint = " The response looks like a landing page; stop the landing project on 5173 and restart JM Camera Sourcing AI." if landing_hint else ""
        print(f"Unexpected frontend content at {args.url}; missing markers: {missing}.{hint}", file=sys.stderr)
        return 1

    print(f"Frontend identity OK at {args.url}: JM Camera Sourcing AI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
