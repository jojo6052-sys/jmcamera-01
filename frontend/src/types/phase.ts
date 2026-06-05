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
  database: string
  metrics: PhaseMetric[]
  ready_checks: Record<string, boolean>
  configuration: PhaseConfiguration
}
