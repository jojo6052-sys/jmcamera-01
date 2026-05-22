import { useEffect, useMemo, useState } from 'react'
import { apiGet, apiPost } from '../api/client'
import type { Candidate, FeedbackRequest, RecommendationScore } from '../types/candidates'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

type RankFilter = '' | 'A' | 'B' | 'C'

export default function RecommendationsPage() {
  const [keyword, setKeyword] = useState('')
  const [rank, setRank] = useState<RankFilter>('')
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
    if (minScore.trim()) params.set('min_score', minScore.trim())
    if (maxPrice.trim()) params.set('max_price', maxPrice.trim())
    const query = params.toString()
    return query ? `?${query}` : ''
  }, [keyword, rank, minScore, maxPrice])

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
    const score = await apiPost<RecommendationScore>(`/api/candidates/${candidateId}/score`, {})
    setScores((prev) => ({ ...prev, [candidateId]: score }))
  }

  async function sendFeedback(candidateId: number, user_decision: FeedbackRequest['user_decision']) {
    await apiPost(`/api/candidates/${candidateId}/feedback`, { user_decision })
    await loadCandidates()
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
                  </td>
                  <td className="p-2">{c.current_price_jpy ?? '-'}</td>
                  <td className="p-2">{c.seller_id || '-'} / {c.seller_rating ?? '-'}</td>
                  <td className="p-2">{score?.total_score ?? '-'}</td>
                  <td className="p-2 font-semibold">{score?.rank ?? '-'}</td>
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
