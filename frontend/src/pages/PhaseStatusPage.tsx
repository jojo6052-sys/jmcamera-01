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

const METRIC_LABELS: Record<string, string> = {
  products: '商品',
  search_keywords: '検索KW',
  yahoo_candidates: 'Yahoo候補',
  recommendation_scores: '推薦スコア',
  feedbacks: 'フィードバック',
  competitor_sellers: 'ライバルセラー',
  competitor_items: 'ライバル商品',
}

export default function PhaseStatusPage() {
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
              <h3 className="font-semibold mb-3">External Configuration</h3>
              <div className="space-y-2 text-sm">
                {Object.entries(status.configuration).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded border border-slate-200 px-3 py-2">
                    <span>{CONFIG_LABELS[key] ?? key}</span>
                    <span className={value ? 'text-emerald-700 font-semibold' : 'text-amber-700 font-semibold'}>{value ? '設定済み' : '未設定'}</span>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-slate-500">未設定でもローカルMVPの確認は可能です。Production連携前に.envへ設定してください。</p>
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
