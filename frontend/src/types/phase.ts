export interface PhaseMetric {
  label: string
  count: number
}

export interface PhaseConfiguration {
  ebay_api_credentials_configured: boolean
  ebay_compliance_configured: boolean
}

export interface PhaseStatus {
  phase: string
  status: string
  core_ready: boolean
  database: string
  metrics: PhaseMetric[]
  ready_checks: Record<string, boolean>
  configuration: PhaseConfiguration
  pending_configuration: string[]
}
