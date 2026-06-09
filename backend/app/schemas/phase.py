from pydantic import BaseModel


class PhaseMetric(BaseModel):
    label: str
    count: int


class PhaseConfiguration(BaseModel):
    ebay_api_credentials_configured: bool
    ebay_compliance_configured: bool


class PhaseStatusRead(BaseModel):
    phase: str
    status: str
    core_ready: bool
    database: str
    metrics: list[PhaseMetric]
    ready_checks: dict[str, bool]
    configuration: PhaseConfiguration
    pending_configuration: list[str]
