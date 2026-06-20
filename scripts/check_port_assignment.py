#!/usr/bin/env python3
"""Validate local port ownership for the JM Camera Sourcing AI dev stack."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FRONTEND_PORT = "5173"
RESERVED_LANDING_PORT = "5174"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    env_example = read(".env.example")
    compose = read("docker-compose.yml")
    vite_config = read("frontend/vite.config.ts")
    package_json = read("frontend/package.json")

    require(
        re.search(r"^FRONTEND_PORT=5173$", env_example, re.MULTILINE) is not None,
        ".env.example must keep FRONTEND_PORT=5173 for the sourcing system.",
        errors,
    )
    require(
        re.search(r"^LANDING_PAGE_PORT=5174$", env_example, re.MULTILINE) is not None,
        ".env.example must reserve LANDING_PAGE_PORT=5174 for the separate landing page project.",
        errors,
    )
    require(
        '"${FRONTEND_PORT:-5173}:5173"' in compose,
        'docker-compose.yml frontend ports must map "${FRONTEND_PORT:-5173}:5173".',
        errors,
    )
    require(
        "container_name: jmcamera_frontend" in compose,
        "docker-compose.yml must use the project-specific jmcamera_frontend container name.",
        errors,
    )
    require(
        re.search(r"port:\s*5173", vite_config) is not None,
        "frontend/vite.config.ts must set server port 5173.",
        errors,
    )
    require(
        re.search(r"strictPort:\s*true", vite_config) is not None,
        "frontend/vite.config.ts must enable strictPort so Vite does not auto-shift to 5174.",
        errors,
    )
    require(
        "--port 5174" not in package_json and "5174" not in package_json,
        "frontend/package.json must not assign the sourcing app to landing page port 5174.",
        errors,
    )

    if errors:
        print("Port assignment check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Port assignment OK: sourcing frontend={EXPECTED_FRONTEND_PORT}, landing page reserved={RESERVED_LANDING_PORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
