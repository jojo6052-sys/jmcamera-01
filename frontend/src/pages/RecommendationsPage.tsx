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
  const [scoringAll, setScoringAll] = useState(false)
  const [batchFeedbacking, setBatchFeedbacking] = useState<FeedbackRequest['user_decision'] | ''>('')
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Set<number>>(new Set())
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)

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
      setCurrentPage(1)
      setSelectedCandidateIds((prev) => {
        const loadedIds = new Set(data.map((candidate) => candidate.id))
        return new Set([...prev].filter((candidateId) => loadedIds.has(candidateId)))
      })
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

  const totalPages = Math.max(1, Math.ceil(candidates.length / pageSize))
  const safeCurrentPage = Math.min(currentPage, totalPages)
  const pageStartIndex = (safeCurrentPage - 1) * pageSize
  const pageCandidates = useMemo(
    () => candidates.slice(pageStartIndex, pageStartIndex + pageSize),
    [candidates, pageStartIndex, pageSize],
  )
  const visibleCandidateIds = useMemo(() => pageCandidates.map((candidate) => candidate.id), [pageCandidates])
  const selectedVisibleCandidateIds = useMemo(
    () => visibleCandidateIds.filter((candidateId) => selectedCandidateIds.has(candidateId)),
    [visibleCandidateIds, selectedCandidateIds],
  )
  const batchTargetCandidateIds = selectedVisibleCandidateIds.length > 0 ? selectedVisibleCandidateIds : visibleCandidateIds
  const allVisibleSelected = visibleCandidateIds.length > 0 && selectedVisibleCandidateIds.length === visibleCandidateIds.length
  const selectedCount = selectedVisibleCandidateIds.length
  const pageEndIndex = Math.min(pageStartIndex + pageCandidates.length, candidates.length)

  function toggleCandidateSelected(candidateId: number) {
    setSelectedCandidateIds((prev) => {
      const next = new Set(prev)
      if (next.has(candidateId)) {
        next.delete(candidateId)
      } else {
        next.add(candidateId)
      }
      return next
    })
  }

  function toggleAllVisibleSelected() {
    setSelectedCandidateIds((prev) => {
      const next = new Set(prev)
      if (allVisibleSelected) {
        visibleCandidateIds.forEach((candidateId) => next.delete(candidateId))
      } else {
        visibleCandidateIds.forEach((candidateId) => next.add(candidateId))
      }
      return next
    })
  }

  async function recalcScore(candidateId: number) {
    setError('')
    try {
      const score = await apiPost<RecommendationScore>(`/api/candidates/${candidateId}/score`, {})
      setScores((prev) => ({ ...prev, [candidateId]: score }))
    } catch {
      setError('推薦スコアの計算に失敗しました')
    }
  }

  async function recalcVisibleScores() {
    if (batchTargetCandidateIds.length === 0) return
    setScoringAll(true)
    setError('')
    try {
      const batchScores = await apiPost<RecommendationScore[]>('/api/candidates/score-batch', {
        candidate_ids: batchTargetCandidateIds,
      })
      setScores((prev) => ({
        ...prev,
        ...Object.fromEntries(batchScores.map((score) => [score.candidate_id, score])),
      }))
    } catch {
      setError('表示中候補の一括スコア計算に失敗しました')
    } finally {
      setScoringAll(false)
    }
  }

  async function sendVisibleFeedback(user_decision: FeedbackRequest['user_decision']) {
    if (batchTargetCandidateIds.length === 0) return
    setBatchFeedbacking(user_decision)
    setError('')
    try {
      await apiPost('/api/candidates/feedback-batch', {
        candidate_ids: batchTargetCandidateIds,
        user_decision,
      })
      await loadCandidates()
    } catch {
      setError('表示中候補の一括フィードバック保存に失敗しました')
    } finally {
      setBatchFeedbacking('')
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

          <div>
            <div className="text-xs text-slate-600 mb-1">表示件数</div>
            <select
              className="border rounded px-3 py-2 w-28"
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setCurrentPage(1)
              }}
            >
              <option value={10}>10件</option>
              <option value={25}>25件</option>
              <option value={50}>50件</option>
              <option value={100}>100件</option>
            </select>
          </div>

          <button className="px-3 py-2 bg-slate-800 text-white rounded" onClick={loadCandidates}>検索</button>
          <button
            className="px-3 py-2 bg-indigo-700 text-white rounded disabled:cursor-not-allowed disabled:bg-indigo-300"
            disabled={scoringAll || batchTargetCandidateIds.length === 0}
            onClick={recalcVisibleScores}
          >
            {scoringAll ? '一括スコア計算中...' : `${selectedCount > 0 ? '選択中' : '表示中'}を一括スコア`}
          </button>
          <button
            className="px-3 py-2 bg-amber-700 text-white rounded disabled:cursor-not-allowed disabled:bg-amber-300"
            disabled={Boolean(batchFeedbacking) || batchTargetCandidateIds.length === 0}
            onClick={() => sendVisibleFeedback('review')}
          >
            {batchFeedbacking === 'review' ? '一括要確認中...' : `${selectedCount > 0 ? '選択中' : '表示中'}を一括要確認`}
          </button>
          <button
            className="px-3 py-2 bg-slate-700 text-white rounded disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={Boolean(batchFeedbacking) || batchTargetCandidateIds.length === 0}
            onClick={() => sendVisibleFeedback('skip')}
          >
            {batchFeedbacking === 'skip' ? '一括見送り中...' : `${selectedCount > 0 ? '選択中' : '表示中'}を一括見送り`}
          </button>
          <a className="px-3 py-2 bg-emerald-700 text-white rounded" href={exportUrl}>CSV出力</a>
        </div>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      {loading && <div className="text-slate-600 text-sm">loading...</div>}
      {!loading && candidates.length > 0 && (
        <div className="text-xs text-slate-600">
          {selectedCount > 0 ? `${selectedCount}件を選択中。一括操作は選択中のみ対象です。` : '未選択の場合、一括操作はこのページに表示中の候補が対象です。'}
        </div>
      )}

      {candidates.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-slate-700">
          <div>
            {candidates.length}件中 {pageStartIndex + 1}〜{pageEndIndex}件を表示（{safeCurrentPage}/{totalPages}ページ）
          </div>
          <div className="space-x-2">
            <button
              className="rounded border px-3 py-1 disabled:cursor-not-allowed disabled:text-slate-300"
              disabled={safeCurrentPage <= 1}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
            >
              前へ
            </button>
            <button
              className="rounded border px-3 py-1 disabled:cursor-not-allowed disabled:text-slate-300"
              disabled={safeCurrentPage >= totalPages}
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
            >
              次へ
            </button>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full bg-white rounded shadow text-sm">
          <thead>
            <tr className="text-left border-b">
              <th className="p-2">
                <input
                  aria-label="表示中候補をすべて選択"
                  checked={allVisibleSelected}
                  onChange={toggleAllVisibleSelected}
                  type="checkbox"
                />
              </th>
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
            {pageCandidates.map((c) => {
              const score = scores[c.id] ?? c.latest_score
              return (
                <tr key={c.id} className="border-b align-top">
                  <td className="p-2">
                    <input
                      aria-label={`${c.title} を選択`}
                      checked={selectedCandidateIds.has(c.id)}
                      onChange={() => toggleCandidateSelected(c.id)}
                      type="checkbox"
                    />
                  </td>
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
