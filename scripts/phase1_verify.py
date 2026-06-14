#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import urllib.error
import urllib.request
from dataclasses import dataclass

import smoke_check


@dataclass(frozen=True)
class VerificationResult:
    name: str
    ok: bool
    detail: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 MVP verification checks against a running local stack.")
    parser.add_argument("--backend-base-url", default="http://localhost:8001", help="Backend base URL. Defaults to http://localhost:8001")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="Frontend URL. Defaults to http://localhost:5173")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout seconds. Defaults to 5")
    parser.add_argument("--skip-write-checks", action="store_true", help="Skip the write smoke flow that creates a keyword, fetches candidates, and scores them.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of human-readable lines.")
    parser.add_argument("--report-file", help="Write a Markdown verification report to this path.")
    args = parser.parse_args()

    results = run_phase1_verification(
        backend_base_url=args.backend_base_url,
        frontend_url=args.frontend_url,
        timeout=args.timeout,
        include_write_checks=not args.skip_write_checks,
    )

    if args.report_file:
        write_markdown_report(Path(args.report_file), results)

    if args.json:
        print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))
    else:
        print_human_results(results)

    return 0 if all(result.ok for result in results) else 1


def print_human_results(results: list[VerificationResult]) -> None:
    for result in results:
        marker = "PASS" if result.ok else "FAIL"
        print(f"[{marker}] {result.name}: {result.detail}")


def write_markdown_report(path: Path, results: list[VerificationResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for result in results if result.ok)
    total = len(results)
    overall = "PASS" if passed == total else "FAIL"
    lines = [
        "# Phase 1 MVP Verification Report",
        "",
        f"Overall: **{overall}** ({passed}/{total} passed)",
        "",
        "| Check | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        lines.append(f"| {escape_markdown_table(result.name)} | {status} | {escape_markdown_table(result.detail)} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def escape_markdown_table(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def run_phase1_verification(
    *,
    backend_base_url: str,
    frontend_url: str,
    timeout: float,
    include_write_checks: bool,
) -> list[VerificationResult]:
    backend_base_url = backend_base_url.rstrip("/")
    frontend_url = frontend_url.rstrip("/")

    results = [
        _run_smoke_check(backend_base_url=backend_base_url, check=check, timeout=timeout)
        for check in smoke_check.READ_ONLY_CHECKS
    ]
    results.append(check_frontend_shell(frontend_url=frontend_url, timeout=timeout))

    if include_write_checks:
        ok, detail = smoke_check.run_write_checks(base_url=backend_base_url, timeout=timeout)
        results.append(VerificationResult(name="write smoke flow", ok=ok, detail=detail))

    return results


def _run_smoke_check(*, backend_base_url: str, check: smoke_check.Check, timeout: float) -> VerificationResult:
    ok, detail = smoke_check.run_check(base_url=backend_base_url, check=check, timeout=timeout)
    return VerificationResult(name=check.name, ok=ok, detail=detail)


def check_frontend_shell(*, frontend_url: str, timeout: float) -> VerificationResult:
    ok, detail, body = request_text(frontend_url.rstrip("/") + "/", timeout=timeout)
    if not ok:
        return VerificationResult(name="frontend shell", ok=False, detail=detail)
    if not looks_like_vite_react_shell(body):
        return VerificationResult(name="frontend shell", ok=False, detail="frontend HTML did not look like the React app shell")
    return VerificationResult(name="frontend shell", ok=True, detail=detail)


def looks_like_vite_react_shell(body: str) -> bool:
    lowered = body.lower()
    return '<div id="root"' in lowered and ("/src/main" in lowered or "/assets/" in lowered)


def request_text(url: str, *, timeout: float) -> tuple[bool, str, str]:
    request = urllib.request.Request(url, method="GET", headers={"Accept": "text/html,application/xhtml+xml,application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            if 200 <= response.status < 300:
                return True, f"HTTP {response.status}", body
            return False, f"HTTP {response.status}; expected 2xx", body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, f"HTTP {exc.code}; expected 2xx", body
    except urllib.error.URLError as exc:
        return False, f"connection error: {exc.reason}", ""
    except TimeoutError:
        return False, "timeout", ""


if __name__ == "__main__":
    sys.exit(main())
