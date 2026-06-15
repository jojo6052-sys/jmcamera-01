import importlib.util
import sys
from pathlib import Path

SMOKE_CHECK_PATH = Path(__file__).resolve().parents[2] / "scripts" / "smoke_check.py"
SMOKE_CHECK_SPEC = importlib.util.spec_from_file_location("smoke_check", SMOKE_CHECK_PATH)
smoke_check = importlib.util.module_from_spec(SMOKE_CHECK_SPEC)
sys.modules[SMOKE_CHECK_SPEC.name] = smoke_check
assert SMOKE_CHECK_SPEC.loader is not None
SMOKE_CHECK_SPEC.loader.exec_module(smoke_check)


def test_validate_phase_status_reports_core_ready_and_pending_configuration() -> None:
    ok, detail = smoke_check.validate_phase_status(
        {
            "database": "ok",
            "status": "ready_with_configuration_pending",
            "core_ready": True,
            "ready_checks": {"database_connected": True},
            "pending_configuration": ["ebay_api_credentials", "ebay_compliance_endpoint"],
        },
        status=200,
    )

    assert ok is True
    assert "status=ready_with_configuration_pending" in detail
    assert "core_ready=True" in detail
    assert "pending_configuration=ebay_api_credentials,ebay_compliance_endpoint" in detail


def test_validate_phase_status_fails_when_core_ready_is_false() -> None:
    ok, detail = smoke_check.validate_phase_status(
        {
            "database": "ok",
            "status": "ready_with_configuration_pending",
            "core_ready": False,
            "ready_checks": {"database_connected": True},
            "pending_configuration": [],
        },
        status=200,
    )

    assert ok is False
    assert "core_ready is not true" in detail
