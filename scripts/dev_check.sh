#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -z "${PYTHON_BIN:-}" ]; then
  for candidate in python3.11 python3.12 python3.13 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)
PY
    then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [ -z "${PYTHON_BIN:-}" ]; then
  echo "Python 3.11-3.13 is required for the pinned backend dependencies." >&2
  exit 1
fi

if command -v git >/dev/null 2>&1; then
  git diff --check
fi

if command -v rg >/dev/null 2>&1; then
  conflict_pattern="$(printf '%s|%s|%s' '<<<''<<<<' '===''====' '>>>''>>>>')"
  if rg -n "$conflict_pattern" README.md scripts backend frontend docker-compose.yml .env.example; then
    echo "Conflict markers found" >&2
    exit 1
  fi
else
  echo "ripgrep (rg) is required for conflict-marker checks" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import ast
from pathlib import Path

source_path = Path("scripts/smoke_check.py")
ast.parse(source_path.read_text(), filename=str(source_path))
PY

cd "$ROOT_DIR/backend"
venv_needs_rebuild=true
if [ -x .venv/bin/python ] && .venv/bin/python - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)
PY
then
  venv_needs_rebuild=false
fi

if [ "$venv_needs_rebuild" = true ]; then
  rm -rf .venv
  "$PYTHON_BIN" -m venv .venv
  .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
fi
DATABASE_URL=sqlite:///./migration_check.db .venv/bin/alembic upgrade head
.venv/bin/python -m compileall app
PYTHONPATH=. .venv/bin/pytest -q

cd "$ROOT_DIR/frontend"
npm install
npm run build

cd "$ROOT_DIR"
rm -rf frontend/dist frontend/tsconfig.tsbuildinfo \
  backend/migration_check.db \
  backend/test_candidates_router.db \
  backend/test_imports_analytics.db \
  backend/test_search_keywords_router.db \
  backend/test_competitors_router.db \
  backend/test_ebay_compliance_router.db \
  backend/test_phase_status.db
find backend -type d -name __pycache__ -prune -exec rm -rf {} +

if [ "${RUN_DOCKER_CHECKS:-false}" = "true" ]; then
  if command -v docker >/dev/null 2>&1; then
    docker compose config >/dev/null
  else
    echo "RUN_DOCKER_CHECKS=true but docker is not available" >&2
    exit 1
  fi
else
  echo "Skipping Docker checks. Set RUN_DOCKER_CHECKS=true to run docker compose config."
fi

echo "dev_check completed successfully"
