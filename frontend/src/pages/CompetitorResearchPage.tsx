import { useEffect, useMemo, useState } from 'react'
import { apiGet, apiPost, apiPostForm } from '../api/client'
import type { CompetitorAnalyzeResponse, CompetitorInsights, CompetitorItem, CompetitorSeller } from '../types/competitors'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

export default function CompetitorResearchPage() {
  const [sellerUrl, setSellerUrl] = useState('')
  const [limit, setLimit] = useState(40)
  const [includeActive, setIncludeActive] = useState(true)
  const [includeSold, setIncludeSold] = useState(true)
  const [htmlFile, setHtmlFile] = useState<File | null>(null)
  const [htmlStatus, setHtmlStatus] = useState<'active' | 'sold'>('sold')
  const [importingHtml, setImportingHtml] = useState(false)
  const [sellers, setSellers] = useState<CompetitorSeller[]>([])
  const [items, setItems] = useState<CompetitorItem[]>([])
  const [insights, setInsights] = useState<CompetitorInsights | null>(null)
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
    if (selectedSellerId) {
      loadItems(selectedSellerId)
      loadInsights(selectedSellerId)
    }
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

  async function loadInsights(sellerId: number) {
    try {
      const payload = await apiGet<CompetitorInsights>(`/api/competitors/${sellerId}/insights`)
      setInsights(payload)
    } catch {
      setError('ライバル分析サマリの取得に失敗しました')
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
      await loadInsights(payload.seller.id)
      await loadSellers()
    } catch (e) {
      setError(e instanceof Error ? `ライバルセラー分析に失敗しました: ${e.message}` : 'ライバルセラー分析に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  async function importSavedHtml() {
    if (!htmlFile) return
    setError(null)
    setMessage(null)
    setImportingHtml(true)
    try {
      const form = new FormData()
      form.append('seller_url', sellerUrl)
      form.append('item_status', htmlStatus)
      form.append('file', htmlFile)
      const payload = await apiPostForm<CompetitorAnalyzeResponse>('/api/competitors/import-html', form)
      setSelectedSellerId(payload.seller.id)
      setItems(payload.items)
      setMessage(`${payload.seller.seller_username} の保存HTMLから ${payload.items.length}件を取り込みました`)
      await loadInsights(payload.seller.id)
      await loadSellers()
    } catch (e) {
      setError(e instanceof Error ? `保存HTMLインポートに失敗しました: ${e.message}` : '保存HTMLインポートに失敗しました')
    } finally {
      setImportingHtml(false)
    }
  }


  async function saveInsightKeyword(keyword: string) {
    if (!selectedSellerId) return
    setError(null)
    setMessage(null)
    try {
      await apiPost(`/api/competitors/${selectedSellerId}/keywords`, {
        keyword,
        category: 'Competitor Research',
        priority: 80,
        active: true,
      })
      setMessage(`検索キーワード「${keyword}」を保存しました`)
    } catch (e) {
      setError(e instanceof Error ? `検索キーワード保存に失敗しました: ${e.message}` : '検索キーワード保存に失敗しました')
    }
  }


  const selectedSeller = useMemo(
    () => sellers.find((seller) => seller.id === selectedSellerId) ?? null,
    [selectedSellerId, sellers],
  )

  const activeCount = items.filter((item) => item.item_status === 'active').length
  const soldCount = items.filter((item) => item.item_status === 'sold').length
  const exportItemsUrl = useMemo(() => {
    if (!selectedSellerId) return '#'
    const params = new URLSearchParams()
    if (statusFilter !== 'all') params.set('item_status', statusFilter)
    if (keyword.trim()) params.set('keyword', keyword.trim())
    const query = params.toString()
    return `${API_BASE_URL}/api/competitors/${selectedSellerId}/export.csv${query ? `?${query}` : ''}`
  }, [keyword, selectedSellerId, statusFilter])

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

      <div className="bg-white p-4 rounded shadow space-y-3">
        <div>
          <h3 className="font-semibold">保存HTMLから取り込み</h3>
          <p className="text-sm text-slate-600">
            eBay画面でSold Itemsを表示して保存したHTMLをアップロードすると、403ブロック時でも履歴を取り込めます。上のセラーURLを入力してから実行してください。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <select className="border rounded px-2 py-2" value={htmlStatus} onChange={(e) => setHtmlStatus(e.target.value as 'active' | 'sold')}>
            <option value="sold">Sold Items HTML</option>
            <option value="active">出品中HTML</option>
          </select>
          <input className="border rounded px-2 py-2" type="file" accept=".html,.htm,text/html" onChange={(e) => setHtmlFile(e.target.files?.[0] ?? null)} />
          <button className="px-3 py-2 bg-indigo-700 text-white rounded disabled:bg-indigo-300" disabled={importingHtml || !sellerUrl.trim() || !htmlFile} onClick={importSavedHtml}>
            {importingHtml ? 'HTML取り込み中...' : '保存HTMLを取り込み'}
          </button>
        </div>
      </div>


      {error && <div className="text-red-600 text-sm">{error}</div>}
      {message && <div className="text-green-700 text-sm">{message}</div>}

      {insights && (
        <div className="grid md:grid-cols-4 gap-3">
          <div className="bg-white rounded shadow p-3">
            <div className="text-xs text-slate-500">Sold比率</div>
            <div className="text-xl font-semibold">{insights.sell_through_rate == null ? '-' : `${insights.sell_through_rate}%`}</div>
          </div>
          <div className="bg-white rounded shadow p-3">
            <div className="text-xs text-slate-500">平均Sold価格</div>
            <div className="text-xl font-semibold">{insights.avg_sold_price == null ? '-' : `$${insights.avg_sold_price}`}</div>
          </div>
          <div className="bg-white rounded shadow p-3">
            <div className="text-xs text-slate-500">Sold - 出品中 価格差</div>
            <div className="text-xl font-semibold">{insights.sold_active_price_gap == null ? '-' : `$${insights.sold_active_price_gap}`}</div>
          </div>
          <div className="bg-white rounded shadow p-3">
            <div className="text-xs text-slate-500">Sold頻出語</div>
            <div className="flex flex-wrap gap-1 text-sm text-slate-700">
              {insights.top_sold_terms.length ? insights.top_sold_terms.map((term) => (
                <button key={term.term} className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200" onClick={() => saveInsightKeyword(term.term)} title="検索キーワードに保存">
                  {term.term}({term.count}) +KW
                </button>
              )) : '-'}
            </div>
          </div>
        </div>
      )}

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
              <a className={`px-3 py-2 rounded ${selectedSellerId ? 'bg-emerald-700 text-white' : 'bg-slate-200 text-slate-500 pointer-events-none'}`} href={exportItemsUrl}>CSV出力</a>
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
