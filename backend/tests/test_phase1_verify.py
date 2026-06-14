import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

PHASE1_VERIFY_PATH = SCRIPTS_DIR / "phase1_verify.py"
PHASE1_VERIFY_SPEC = importlib.util.spec_from_file_location("phase1_verify", PHASE1_VERIFY_PATH)
phase1_verify = importlib.util.module_from_spec(PHASE1_VERIFY_SPEC)
sys.modules[PHASE1_VERIFY_SPEC.name] = phase1_verify
assert PHASE1_VERIFY_SPEC.loader is not None
PHASE1_VERIFY_SPEC.loader.exec_module(phase1_verify)


def test_looks_like_vite_react_shell_accepts_dev_shell() -> None:
    body = '<!doctype html><div id="root"></div><script type="module" src="/src/main.tsx"></script>'

    assert phase1_verify.looks_like_vite_react_shell(body) is True


def test_looks_like_vite_react_shell_accepts_built_shell() -> None:
    body = '<!doctype html><div id="root"></div><script type="module" src="/assets/index.js"></script>'

    assert phase1_verify.looks_like_vite_react_shell(body) is True


def test_looks_like_vite_react_shell_rejects_non_app_html() -> None:
    assert phase1_verify.looks_like_vite_react_shell("<html><body>not the app</body></html>") is False


def test_write_markdown_report_records_overall_and_escapes_table_values(tmp_path) -> None:
    report_path = tmp_path / "reports" / "phase1.md"
    phase1_verify.write_markdown_report(
        report_path,
        [
            phase1_verify.VerificationResult(name="backend|health", ok=True, detail="HTTP 200"),
            phase1_verify.VerificationResult(name="frontend", ok=False, detail="bad|html"),
        ],
    )

    report = report_path.read_text(encoding="utf-8")
    assert "Overall: **FAIL** (1/2 passed)" in report
    assert "backend\\|health" in report
    assert "bad\\|html" in report
