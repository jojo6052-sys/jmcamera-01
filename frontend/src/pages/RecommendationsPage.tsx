import { useEffect, useMemo, useState } from 'react'
import { apiGet, apiPost } from '../api/client'
import type { Candidate, FeedbackRequest, RecommendationScore } from '../types/candidates'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

type RankFilter = '' | 'A' | 'B' | 'C'
type StatusFilter = '' | 'new' | 'purchase' | 'review' | 'skip'

function formatNumber(value: number | null | undefined, digits = 0) {
  if (value === null || value === undefined) return '-'
  return value.toLocaleString('ja-JP', { maximumFractionDigits: digits })
}

function formatJpy(value: number | null | undefined) {
  const formatted = formatNumber(value)
  return formatted === '-' ? formatted : `¥${formatted}`
}

function formatPercent(value: number | null | undefined) {
  const formatted = formatNumber(value, 1)
  return formatted === '-' ? formatted : `${formatted}%`
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    new: '未判断',
    purchase: '仕入れ',
    review: '要確認',
    skip: '見送り',
  }
  return labels[status] ?? status
}

export default function RecommendationsPage() {
  const [keyword, setKeyword] = useState('')
  const [rank, setRank] = useState<RankFilter>('')
  const [status, setStatus] = useState<StatusFilter>('')
  const [minScore, setMinScore] = useState('')
  const [maxPrice, setMaxPrice] = useState('')

  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [scores, setScores] = useState<Record<number, RecommendationScore>>({})

  const queryString = useMemo(() => {
    const params = new URLSearchParams()
    if (keyword.trim()) params.set('keyword', keyword.trim())
    if (rank) params.set('rank', rank)
    if (status) params.set('status', status)
    if (minScore.trim()) params.set('min_score', minScore.trim())
    if (maxPrice.trim()) params.set('max_price', maxPrice.trim())
    const query = params.toString()
    return query ? `?${query}` : ''
  }, [keyword, rank, status, minScore, maxPrice])

  async function loadCandidates() {
    setLoading(true)
    setError('')
    try {
      const data = await apiGet<Candidate[]>(`/api/candidates${queryString}`)
      setCandidates(data)
    } catch {
      setError('候補一覧の取得に失敗しました')
      setCandidates([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCandidates()
  }, [])

  async function recalcScore(candidateId: number) {
    setError('')
    try {
      const score = await apiPost<RecommendationScore>(`/api/candidates/${candidateId}/score`, {})
      setScores((prev) => ({ ...prev, [candidateId]: score }))
    } catch {
      setError('推薦スコアの計算に失敗しました')
    }
  }

  async function sendFeedback(candidateId: number, user_decision: FeedbackRequest['user_decision']) {
    setError('')
    try {
      await apiPost(`/api/candidates/${candidateId}/feedback`, { user_decision })
      await loadCandidates()
    } catch {
      setError('フィードバック保存に失敗しました')
    }
  }

  const exportUrl = `${API_BASE_URL}/api/candidates/export.csv${queryString}`

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow space-y-3">
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <div className="text-xs text-slate-600 mb-1">キーワード</div>
            <input
              className="border rounded px-3 py-2 w-64"
              placeholder="例: Canon EOS"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>

          <div>
            <div className="text-xs text-slate-600 mb-1">ランク</div>
            <select className="border rounded px-3 py-2 w-24" value={rank} onChange={(e) => setRank(e.target.value as RankFilter)}>
              <option value="">All</option>
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
            </select>
          </div>

          <div>
            <div className="text-xs text-slate-600 mb-1">判定ステータス</div>
            <select className="border rounded px-3 py-2 w-32" value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)}>
              <option value="">All</option>
              <option value="new">未判断</option>
              <option value="purchase">仕入れ</option>
              <option value="review">要確認</option>
              <option value="skip">見送り</option>
            </select>
          </div>

          <div>
            <div className="text-xs text-slate-600 mb-1">最小スコア</div>
            <input
              className="border rounded px-3 py-2 w-28"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
            />
          </div>

          <div>
            <div className="text-xs text-slate-600 mb-1">上限価格</div>
            <input
              className="border rounded px-3 py-2 w-32"
              type="number"
              min="0"
              step="1"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
          </div>

          <button className="px-3 py-2 bg-slate-800 text-white rounded" onClick={loadCandidates}>検索</button>
          <a className="px-3 py-2 bg-emerald-700 text-white rounded" href={exportUrl}>CSV出力</a>
        </div>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      {loading && <div className="text-slate-600 text-sm">loading...</div>}

      <div className="overflow-x-auto">
        <table className="w-full bg-white rounded shadow text-sm">
          <thead>
            <tr className="text-left border-b">
              <th className="p-2">Title</th>
              <th className="p-2">Current</th>
              <th className="p-2">Seller</th>
              <th className="p-2">Status</th>
              <th className="p-2">Score</th>
              <th className="p-2">Rank</th>
              <th className="p-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => {
              const score = scores[c.id]
              return (
                <tr key={c.id} className="border-b align-top">
                  <td className="p-2">
                    <a href={c.url} target="_blank" rel="noreferrer" className="text-blue-700 hover:underline">
                      {c.title}
                    </a>
                    <div className="text-xs text-slate-500">{c.search_keyword || '-'}</div>
                    {score && (
                      <div className="mt-2 rounded bg-slate-50 p-2 text-xs text-slate-700">
                        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                          <div><span className="font-semibold">想定売価:</span> {formatJpy(score.expected_sale_price_jpy)}</div>
                          <div><span className="font-semibold">想定利益:</span> {formatJpy(score.expected_profit_jpy)}</div>
                          <div><span className="font-semibold">利益率:</span> {formatPercent(score.expected_profit_margin)}</div>
                          <div><span className="font-semibold">推奨上限入札:</span> {formatJpy(score.recommended_max_bid_jpy)}</div>
                          <div><span className="font-semibold">類似度:</span> {formatNumber(score.similarity_score, 1)}</div>
                          <div><span className="font-semibold">出品者リスク:</span> {formatNumber(score.seller_risk_score, 1)}</div>
                          <div><span className="font-semibold">説明リスク:</span> {formatNumber(score.description_risk_score, 1)}</div>
                          <div><span className="font-semibold">画像リスク:</span> {formatNumber(score.image_risk_score, 1)}</div>
                        </div>
                        {score.reason && <div className="mt-2"><span className="font-semibold">理由:</span> {score.reason}</div>}
                        {score.caution && <div className="mt-1 text-amber-700"><span className="font-semibold">注意:</span> {score.caution}</div>}
                      </div>
                    )}
                  </td>
                  <td className="p-2">{c.current_price_jpy ?? '-'}</td>
                  <td className="p-2">{c.seller_id || '-'} / {c.seller_rating ?? '-'}</td>
                  <td className="p-2"><span className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{statusLabel(c.status)}</span></td>
                  <td className="p-2">{score?.total_score ?? c.latest_total_score ?? '-'}</td>
                  <td className="p-2 font-semibold">{score?.rank ?? c.latest_rank ?? '-'}</td>
                  <td className="p-2 space-x-1">
                    <button className="px-2 py-1 bg-indigo-600 text-white rounded" onClick={() => recalcScore(c.id)}>Score</button>
                    <button className="px-2 py-1 bg-green-600 text-white rounded" onClick={() => sendFeedback(c.id, 'purchase')}>仕入れ</button>
                    <button className="px-2 py-1 bg-amber-600 text-white rounded" onClick={() => sendFeedback(c.id, 'review')}>要確認</button>
                    <button className="px-2 py-1 bg-slate-600 text-white rounded" onClick={() => sendFeedback(c.id, 'skip')}>見送り</button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
