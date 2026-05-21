import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../api/client'
import type { Candidate, FeedbackRequest, RecommendationScore } from '../types/candidates'

export default function RecommendationsPage() {
  const [keyword, setKeyword] = useState('')
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [scores, setScores] = useState<Record<number, RecommendationScore>>({})

  async function loadCandidates() {
    setLoading(true)
    setError('')
    try {
      const query = keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''
      const data = await apiGet<Candidate[]>(`/api/candidates${query}`)
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

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow flex items-center gap-2">
        <input
          className="border rounded px-3 py-2 w-96"
          placeholder="keyword filter"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
        <button className="px-3 py-2 bg-slate-800 text-white rounded" onClick={loadCandidates}>検索</button>
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
