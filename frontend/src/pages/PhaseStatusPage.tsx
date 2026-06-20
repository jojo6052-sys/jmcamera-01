import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'
import type { PhaseStatus } from '../types/phase'

const CHECK_LABELS: Record<string, string> = {
  database_connected: 'DB接続',
  csv_import_ready: 'CSVインポート',
  analytics_ready: '分析APIデータ',
  search_keywords_ready: '検索KW管理',
  yahoo_candidates_ready: 'Yahoo候補',
  recommendation_scoring_ready: '推薦スコア',
  competitor_research_ready: 'ライバル分析',
  ebay_compliance_endpoint_ready: 'eBay削除通知設定',
}

const CONFIG_LABELS: Record<string, string> = {
  ebay_api_credentials_configured: 'eBay API credentials',
  ebay_compliance_configured: 'eBay削除通知endpoint',
}

const PENDING_CONFIG_LABELS: Record<string, string> = {
  ebay_api_credentials: 'eBay API credentials',
  ebay_compliance_endpoint: 'eBay削除通知endpoint',
}

const METRIC_LABELS: Record<string, string> = {
  products: '商品',
  search_keywords: '検索KW',
  yahoo_candidates: 'Yahoo候補',
  recommendation_scores: '推薦スコア',
  feedbacks: 'フィードバック',
  competitor_sellers: 'ライバルセラー',
  competitor_items: 'ライバル商品',
}

type PhaseStatusPageProps = {
  onOpenGuide?: () => void
}

function getNextActions(status: PhaseStatus): string[] {
  if (!status.core_ready) {
    return [
      'Ready Checks の「要確認」項目を確認し、backend pytest / frontend build / smoke check を再実行してください。',
      'DB接続や主要データ件数に問題がある場合は、Compose起動状態とマイグレーション結果を確認してください。',
    ]
  }

  if (status.pending_configuration.length > 0) {
    return [
      'ローカルMVPは確認可能です。次は System Manual の流れに沿ってCSVインポート、候補取得、推薦判断を確認してください。',
      'Production化する前に、未設定の eBay API credentials / Marketplace Account Deletion endpoint を準備してください。',
    ]
  }

  return [
    'ローカルMVPとProduction向け設定がそろっています。Phase verification reportを保存し、PRレビューまたは運用検証へ進んでください。',
  ]
}

export default function PhaseStatusPage({ onOpenGuide }: PhaseStatusPageProps) {
  const [status, setStatus] = useState<PhaseStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function loadStatus() {
    setLoading(true)
    setError(null)
    try {
      setStatus(await apiGet<PhaseStatus>('/api/phase/status'))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Phase status の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  return (
    <div className="space-y-4">
      <div className="bg-white rounded shadow p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">MVP Phase Status</h2>
          <p className="text-sm text-slate-600">backend / DB / 主要APIのPhase完了確認用ダッシュボードです。</p>
        </div>
        <button className="px-3 py-2 rounded bg-slate-800 text-white disabled:bg-slate-300" disabled={loading} onClick={loadStatus}>
          {loading ? '確認中...' : '再確認'}
        </button>
      </div>

      {error && <div className="bg-red-50 text-red-700 border border-red-200 rounded p-3 text-sm">{error}</div>}

      {status && (
        <>
          <div className="grid md:grid-cols-3 gap-3">
            <div className="bg-white rounded shadow p-4">
              <div className="text-xs text-slate-500">Phase</div>
              <div className="text-2xl font-semibold">{status.phase}</div>
            </div>
            <div className="bg-white rounded shadow p-4">
              <div className="text-xs text-slate-500">Status</div>
              <div className={status.status === 'ready' ? 'text-2xl font-semibold text-emerald-700' : 'text-2xl font-semibold text-amber-700'}>{status.status}</div>
              <div className={status.core_ready ? 'mt-1 text-xs font-medium text-emerald-700' : 'mt-1 text-xs font-medium text-red-700'}>
                {status.core_ready ? 'Local MVP ready' : 'Core checks need attention'}
              </div>
            </div>
            <div className="bg-white rounded shadow p-4">
              <div className="text-xs text-slate-500">Database</div>
              <div className="text-2xl font-semibold">{status.database}</div>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <div className="bg-white rounded shadow p-4">
              <h3 className="font-semibold mb-3">Ready Checks</h3>
              <div className="grid sm:grid-cols-2 gap-2 text-sm">
                {Object.entries(status.ready_checks).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded border border-slate-200 px-3 py-2">
                    <span>{CHECK_LABELS[key] ?? key}</span>
                    <span className={value ? 'text-emerald-700 font-semibold' : 'text-amber-700 font-semibold'}>{value ? 'OK' : '要確認'}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded shadow p-4">
              <h3 className="font-semibold mb-3">Production Configuration</h3>
              <div className="space-y-2 text-sm">
                {Object.entries(status.configuration).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded border border-slate-200 px-3 py-2">
                    <span>{CONFIG_LABELS[key] ?? key}</span>
                    <span className={value ? 'text-emerald-700 font-semibold' : 'text-amber-700 font-semibold'}>{value ? '設定済み' : '未設定'}</span>
                  </div>
                ))}
              </div>
              {status.pending_configuration.length > 0 ? (
                <p className="mt-3 text-xs text-slate-500">
                  未設定: {status.pending_configuration.map((key) => PENDING_CONFIG_LABELS[key] ?? key).join('、')}。ローカルMVP確認は完了扱いにできます。
                </p>
              ) : (
                <p className="mt-3 text-xs text-emerald-700">Production連携設定も完了しています。</p>
              )}
            </div>


            <div className="bg-white rounded shadow p-4 lg:col-span-2">
              <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                <div>
                  <h3 className="font-semibold">Recommended Next Actions</h3>
                  <p className="text-xs text-slate-500">現在のPhase statusに応じた次の確認ポイントです。</p>
                </div>
                {onOpenGuide && (
                  <button className="px-3 py-2 rounded bg-slate-800 text-white text-sm" onClick={onOpenGuide}>
                    System Manualを開く
                  </button>
                )}
              </div>
              <ol className="list-decimal pl-5 space-y-2 text-sm text-slate-700 leading-6">
                {getNextActions(status).map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ol>
            </div>

            <div className="bg-white rounded shadow p-4 lg:col-span-2">
              <h3 className="font-semibold mb-3">Data Counts</h3>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 text-sm">
                {status.metrics.map((metric) => (
                  <div key={metric.label} className="flex items-center justify-between rounded border border-slate-200 px-3 py-2">
                    <span>{METRIC_LABELS[metric.label] ?? metric.label}</span>
                    <span className="font-semibold">{metric.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
