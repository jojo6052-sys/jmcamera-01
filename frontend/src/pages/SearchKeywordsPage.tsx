import { useEffect, useState } from 'react'
import { apiDelete, apiGet, apiPost, apiPut } from '../api/client'
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
    if (!form.keyword?.trim()) return
    await apiPost('/api/search-keywords', {
      ...form,
      keyword: form.keyword.trim(),
      category: form.category || null,
      brand: form.brand || null,
      model_group: form.model_group || null,
    })
    setForm(initialForm)
    await load()
  }

  async function toggleActive(item: SearchKeyword) {
    await apiPut(`/api/search-keywords/${item.id}`, { active: !item.active })
    await load()
  }

  async function remove(item: SearchKeyword) {
    await apiDelete(`/api/search-keywords/${item.id}`)
    await load()
  }

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow grid grid-cols-6 gap-2">
        <input className="border rounded px-2 py-2 col-span-2" placeholder="keyword" value={form.keyword || ''} onChange={(e) => setForm({ ...form, keyword: e.target.value })} />
        <input className="border rounded px-2 py-2" placeholder="category" value={form.category || ''} onChange={(e) => setForm({ ...form, category: e.target.value })} />
        <input className="border rounded px-2 py-2" placeholder="brand" value={form.brand || ''} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
        <input className="border rounded px-2 py-2" placeholder="model group" value={form.model_group || ''} onChange={(e) => setForm({ ...form, model_group: e.target.value })} />
        <input className="border rounded px-2 py-2" type="number" placeholder="priority" value={form.priority ?? 100} onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })} />
        <button className="px-3 py-2 bg-slate-800 text-white rounded" onClick={createKeyword}>追加</button>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
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
