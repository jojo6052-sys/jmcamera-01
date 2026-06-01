import { useEffect, useState } from 'react'
import { apiDelete, apiGet, apiPost, apiPut } from '../api/client'
import type { Candidate } from '../types/candidates'
import type { SearchKeyword, SearchKeywordCreate } from '../types/keywords'

const initialForm: SearchKeywordCreate = {
  keyword: '',
  category: '',
  brand: '',
  model_group: '',
  priority: 100,
  active: true,
}

export default function SearchKeywordsPage() {
  const [items, setItems] = useState<SearchKeyword[]>([])
  const [form, setForm] = useState<SearchKeywordCreate>(initialForm)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [fetchingKeywordId, setFetchingKeywordId] = useState<number | null>(null)
  const [fetchMessage, setFetchMessage] = useState('')
  const [candidateLimit, setCandidateLimit] = useState(10)
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [excludeWords, setExcludeWords] = useState('ジャンク,故障')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const data = await apiGet<SearchKeyword[]>('/api/search-keywords')
      setItems(data)
    } catch {
      setError('キーワード一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function createKeyword() {
    if (!form.keyword?.trim()) {
      setError('キーワードを入力してください')
      return
    }

    setLoading(true)
    setError('')
    setFetchMessage('')
    try {
      await apiPost('/api/search-keywords', {
        ...form,
        keyword: form.keyword.trim(),
        category: form.category || null,
        brand: form.brand || null,
        model_group: form.model_group || null,
      })
      setForm(initialForm)
      await load()
    } catch (err) {
      setError(`キーワードの追加に失敗しました: ${err instanceof Error ? err.message : '既に登録済みのキーワードでないか確認してください。'}`)
    } finally {
      setLoading(false)
    }
  }

  async function toggleActive(item: SearchKeyword) {
    await apiPut(`/api/search-keywords/${item.id}`, { active: !item.active })
    await load()
  }

  async function remove(item: SearchKeyword) {
    await apiDelete(`/api/search-keywords/${item.id}`)
    await load()
  }

  async function fetchCandidates(item: SearchKeyword) {
    setFetchingKeywordId(item.id)
    setError('')
    setFetchMessage('')
    try {
      const candidates = await apiPost<Candidate[]>('/api/yahoo/search', {
        keyword: item.keyword,
        limit: candidateLimit,
        min_price: minPrice ? Number(minPrice) : null,
        max_price: maxPrice ? Number(maxPrice) : null,
        exclude_words: excludeWords.split(',').map((word) => word.trim()).filter(Boolean),
      })
      setFetchMessage(`${item.keyword}: ${candidates.length}件の候補を保存しました。Recommendationsで確認できます。`)
    } catch (err) {
      setError(`ヤフオク候補取得に失敗しました: ${err instanceof Error ? err.message : 'unknown error'}`)
    } finally {
      setFetchingKeywordId(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow space-y-3">
        <h2 className="text-lg font-semibold">検索キーワード登録</h2>
        <div className="grid grid-cols-6 gap-2">
          <input className="border rounded px-2 py-2 col-span-2" placeholder="keyword" value={form.keyword || ''} onChange={(e) => setForm({ ...form, keyword: e.target.value })} />
          <input className="border rounded px-2 py-2" placeholder="category" value={form.category || ''} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          <input className="border rounded px-2 py-2" placeholder="brand" value={form.brand || ''} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
          <input className="border rounded px-2 py-2" placeholder="model group" value={form.model_group || ''} onChange={(e) => setForm({ ...form, model_group: e.target.value })} />
          <input className="border rounded px-2 py-2" type="number" placeholder="priority" value={form.priority ?? 100} onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })} />
          <button className="px-3 py-2 bg-slate-800 text-white rounded disabled:bg-slate-400" disabled={loading} onClick={createKeyword}>{loading ? '追加中...' : '追加'}</button>
        </div>
      </div>

      <div className="bg-white p-4 rounded shadow space-y-3">
        <h2 className="text-lg font-semibold">ヤフオク候補取得条件</h2>
        <div className="grid grid-cols-4 gap-2">
          <label className="text-sm">
            取得件数
            <input className="border rounded px-2 py-2 w-full mt-1" type="number" min="1" max="50" value={candidateLimit} onChange={(e) => setCandidateLimit(Number(e.target.value))} />
          </label>
          <label className="text-sm">
            最低価格
            <input className="border rounded px-2 py-2 w-full mt-1" type="number" min="0" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} />
          </label>
          <label className="text-sm">
            最高価格
            <input className="border rounded px-2 py-2 w-full mt-1" type="number" min="0" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />
          </label>
          <label className="text-sm">
            除外ワード（カンマ区切り）
            <input className="border rounded px-2 py-2 w-full mt-1" value={excludeWords} onChange={(e) => setExcludeWords(e.target.value)} />
          </label>
        </div>
        <p className="text-xs text-slate-500">各キーワード行の「候補取得」から、この条件で候補を保存します。</p>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      {fetchMessage && <div className="text-green-700 text-sm">{fetchMessage}</div>}
      {loading && <div className="text-slate-500 text-sm">loading...</div>}

      <table className="w-full bg-white rounded shadow text-sm">
        <thead>
          <tr className="text-left border-b">
            <th className="p-2">Keyword</th>
            <th className="p-2">Category</th>
            <th className="p-2">Brand</th>
            <th className="p-2">Priority</th>
            <th className="p-2">Active</th>
            <th className="p-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b">
              <td className="p-2">{item.keyword}</td>
              <td className="p-2">{item.category || '-'}</td>
              <td className="p-2">{item.brand || '-'}</td>
              <td className="p-2">{item.priority}</td>
              <td className="p-2">{item.active ? 'ON' : 'OFF'}</td>
              <td className="p-2 space-x-2">
                <button className="px-2 py-1 bg-emerald-700 text-white rounded disabled:bg-slate-400" disabled={fetchingKeywordId === item.id} onClick={() => fetchCandidates(item)}>
                  {fetchingKeywordId === item.id ? '取得中...' : '候補取得'}
                </button>
                <button className="px-2 py-1 bg-indigo-600 text-white rounded" onClick={() => toggleActive(item)}>
                  Toggle
                </button>
                <button className="px-2 py-1 bg-rose-600 text-white rounded" onClick={() => remove(item)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
