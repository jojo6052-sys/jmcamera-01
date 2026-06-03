import { useEffect, useMemo, useState } from 'react'
import { apiGet, apiPost } from '../api/client'
import type { CompetitorAnalyzeResponse, CompetitorItem, CompetitorSeller } from '../types/competitors'

export default function CompetitorResearchPage() {
  const [sellerUrl, setSellerUrl] = useState('')
  const [limit, setLimit] = useState(40)
  const [includeActive, setIncludeActive] = useState(true)
  const [includeSold, setIncludeSold] = useState(true)
  const [sellers, setSellers] = useState<CompetitorSeller[]>([])
  const [items, setItems] = useState<CompetitorItem[]>([])
  const [selectedSellerId, setSelectedSellerId] = useState<number | null>(null)
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'sold'>('all')
  const [keyword, setKeyword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    loadSellers()
  }, [])

  useEffect(() => {
    if (selectedSellerId) loadItems(selectedSellerId)
  }, [selectedSellerId, statusFilter])

  async function loadSellers() {
    try {
      const rows = await apiGet<CompetitorSeller[]>('/api/competitors')
      setSellers(rows)
      if (!selectedSellerId && rows.length > 0) setSelectedSellerId(rows[0].id)
    } catch {
      setError('ライバルセラー一覧の取得に失敗しました')
    }
  }

  async function loadItems(sellerId: number) {
    try {
      const params = new URLSearchParams()
      if (statusFilter !== 'all') params.set('item_status', statusFilter)
      if (keyword.trim()) params.set('keyword', keyword.trim())
      const query = params.toString()
      const rows = await apiGet<CompetitorItem[]>(`/api/competitors/${sellerId}/items${query ? `?${query}` : ''}`)
      setItems(rows)
    } catch {
      setError('ライバル商品一覧の取得に失敗しました')
    }
  }

  async function analyzeSeller() {
    setError(null)
    setMessage(null)
    setLoading(true)
    try {
      const payload = await apiPost<CompetitorAnalyzeResponse>('/api/competitors/analyze', {
        seller_url: sellerUrl,
        include_active: includeActive,
        include_sold: includeSold,
        limit,
      })
      setSelectedSellerId(payload.seller.id)
      setItems(payload.items)
      setMessage(`${payload.seller.seller_username} から ${payload.items.length}件を取り込みました`)
      await loadSellers()
    } catch (e) {
      setError(e instanceof Error ? `ライバルセラー分析に失敗しました: ${e.message}` : 'ライバルセラー分析に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const selectedSeller = useMemo(
    () => sellers.find((seller) => seller.id === selectedSellerId) ?? null,
    [selectedSellerId, sellers],
  )

  const activeCount = items.filter((item) => item.item_status === 'active').length
  const soldCount = items.filter((item) => item.item_status === 'sold').length

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow space-y-3">
        <div>
          <h2 className="text-xl font-semibold">Competitor Research</h2>
          <p className="text-sm text-slate-600">
            eBayセラーURLを入れると、出品中商品とSold Itemsの履歴を取り込み、相場・売れ筋の比較用データとして保存します。
          </p>
        </div>
        <div className="grid md:grid-cols-[1fr_120px] gap-2">
          <input
            className="border rounded px-3 py-2"
            placeholder="https://www.ebay.com/str/example-seller"
            value={sellerUrl}
            onChange={(e) => setSellerUrl(e.target.value)}
          />
          <input
            className="border rounded px-3 py-2"
            type="number"
            min="1"
            max="100"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          />
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-1"><input type="checkbox" checked={includeActive} onChange={(e) => setIncludeActive(e.target.checked)} />出品中</label>
          <label className="flex items-center gap-1"><input type="checkbox" checked={includeSold} onChange={(e) => setIncludeSold(e.target.checked)} />Sold Items</label>
          <button className="px-3 py-2 bg-slate-800 text-white rounded disabled:bg-slate-300" disabled={loading || !sellerUrl.trim() || (!includeActive && !includeSold)} onClick={analyzeSeller}>
            {loading ? '分析中...' : 'ライバルを分析'}
          </button>
        </div>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      {message && <div className="text-green-700 text-sm">{message}</div>}

      <div className="grid lg:grid-cols-[320px_1fr] gap-4">
        <div className="bg-white rounded shadow p-4 space-y-3">
          <h3 className="font-semibold">保存済みセラー</h3>
          {sellers.length === 0 && <div className="text-sm text-slate-500">まだセラーがありません</div>}
          <div className="space-y-2">
            {sellers.map((seller) => (
              <button key={seller.id} className={`w-full text-left border rounded p-3 ${seller.id === selectedSellerId ? 'border-slate-800 bg-slate-50' : 'border-slate-200'}`} onClick={() => setSelectedSellerId(seller.id)}>
                <div className="font-medium">{seller.seller_username}</div>
                <div className="text-xs text-slate-600">出品中 {seller.active_count} / Sold {seller.sold_count}</div>
                <div className="text-xs text-slate-500">平均: active ${seller.avg_active_price ?? '-'} / sold ${seller.avg_sold_price ?? '-'}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded shadow p-4 space-y-3">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h3 className="font-semibold">{selectedSeller ? `${selectedSeller.seller_username} の商品` : '商品'}</h3>
              <div className="text-xs text-slate-600">表示中: 出品中 {activeCount} / Sold {soldCount}</div>
              {selectedSeller?.fetch_status === 'blocked' && <div className="text-xs text-amber-700">eBay側で自動取得が403ブロックされました。URLは認識できていますが、この環境からの直接取得が拒否されています。</div>}
              {selectedSeller?.last_error && <div className="text-xs text-amber-700">取得エラー: {selectedSeller.last_error}</div>}
            </div>
            <div className="flex gap-2">
              <select className="border rounded px-2 py-2" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'sold')}>
                <option value="all">すべて</option>
                <option value="active">出品中</option>
                <option value="sold">Sold</option>
              </select>
              <input className="border rounded px-2 py-2" placeholder="キーワード" value={keyword} onChange={(e) => setKeyword(e.target.value)} />
              <button className="px-3 py-2 bg-slate-700 text-white rounded" disabled={!selectedSellerId} onClick={() => selectedSellerId && loadItems(selectedSellerId)}>検索</button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2 pr-2">画像</th>
                  <th className="py-2 pr-2">タイトル</th>
                  <th className="py-2 pr-2">状態</th>
                  <th className="py-2 pr-2">価格</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b align-top">
                    <td className="py-2 pr-2 w-20">{item.image_url ? <img className="h-14 w-14 object-cover rounded" src={item.image_url} alt="" /> : <div className="h-14 w-14 bg-slate-100 rounded" />}</td>
                    <td className="py-2 pr-2"><a className="text-blue-700 hover:underline" href={item.item_url} target="_blank" rel="noreferrer">{item.title}</a></td>
                    <td className="py-2 pr-2"><span className={`px-2 py-1 rounded text-xs ${item.item_status === 'sold' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}`}>{item.item_status === 'sold' ? 'Sold' : '出品中'}</span></td>
                    <td className="py-2 pr-2 whitespace-nowrap">{item.price != null ? `${item.currency ?? ''} ${item.price}` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
