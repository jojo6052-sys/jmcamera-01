import { useEffect, useState } from 'react'
import { apiGet, apiPostForm } from '../api/client'
import type { BestSellerItem, CategoryAnalyticsItem } from '../types/analytics'
import type { ProductImportResponse } from '../types/imports'


const sampleProductsCsv = [
  'es_number,title,normalized_title,brand,model,category,mount,condition_rank,purchase_price_jpy,sale_price_usd,sale_price_jpy,gross_profit_jpy,final_profit_jpy,profit_margin,purchased_at,listed_at,sold_at,days_to_sell,sales_channel,buyer_country,returned,complaint,repair_required,seller_id,source_platform,source_url,notes',
  'ES-001,Canon EOS 5D,canon eos 5d,Canon,EOS 5D,Camera,EF,B,45000,650,95000,50000,42000,44.2,2026-05-01,2026-05-03,2026-05-12,9,eBay,US,false,false,false,seller-a,Yahoo Auctions,https://example.com/a,Sample row',
  'ES-002,Nikon F3 Body,nikon f3 body,Nikon,F3,Film Camera,F,A,28000,420,62000,34000,28000,45.1,2026-05-02,2026-05-04,2026-05-20,16,eBay,CA,false,false,false,seller-b,Yahoo Auctions,https://example.com/b,Sample row',
].join('\n')

export default function ProductAnalyticsPage() {
  const [bestSellers, setBestSellers] = useState<BestSellerItem[]>([])
  const [categories, setCategories] = useState<CategoryAnalyticsItem[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [importMessage, setImportMessage] = useState('')

  async function loadAnalytics() {
    setLoading(true)
    setError('')
    try {
      const [bestSellerData, categoryData] = await Promise.all([
        apiGet<BestSellerItem[]>('/api/analytics/best-sellers'),
        apiGet<CategoryAnalyticsItem[]>('/api/analytics/categories'),
      ])
      setBestSellers(bestSellerData)
      setCategories(categoryData)
    } catch {
      setError('分析データの取得に失敗しました')
      setBestSellers([])
      setCategories([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalytics()
  }, [])

  function downloadSampleCsv() {
    const blob = new Blob([sampleProductsCsv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'jm-camera-products-sample.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  async function uploadProductsCsv() {
    if (!file) {
      setError('CSVファイルを選択してください')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    setError('')
    setImportMessage('')
    try {
      const result = await apiPostForm<ProductImportResponse>('/api/import/products', formData)
      setImportMessage(`CSVインポート完了: ${result.imported_count}件追加 / ${result.skipped_count}件スキップ`)
      setFile(null)
      await loadAnalytics()
    } catch (err) {
      setError(`CSVインポートに失敗しました: ${err instanceof Error ? err.message : 'unknown error'}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-8">
      <section className="bg-white p-4 rounded shadow space-y-3">
        <h2 className="text-xl font-semibold">Product CSV Import</h2>
        <p className="text-sm text-slate-600">
          売上・仕入れ実績CSVを取り込むと、Best Sellers と Category Analytics が更新されます。
          必須列は <code className="bg-slate-100 px-1 rounded">title</code> です。
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <input
            className="block text-sm"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button
            className="px-3 py-2 bg-slate-800 text-white rounded disabled:bg-slate-400"
            disabled={uploading || !file}
            onClick={uploadProductsCsv}
          >
            {uploading ? 'インポート中...' : 'CSVインポート'}
          </button>
          <button className="px-3 py-2 bg-slate-100 rounded" onClick={downloadSampleCsv}>
            サンプルCSVダウンロード
          </button>
          <button className="px-3 py-2 bg-slate-100 rounded disabled:text-slate-400" disabled={loading || uploading} onClick={loadAnalytics}>
            再読み込み
          </button>
        </div>
        {file && <div className="text-xs text-slate-500">選択中: {file.name}</div>}
        {importMessage && <div className="text-green-700 text-sm">{importMessage}</div>}
        {error && <div className="text-red-600 text-sm">{error}</div>}
        {loading && <div className="text-slate-500 text-sm">loading...</div>}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">Best Sellers</h2>
        <table className="w-full bg-white rounded shadow text-sm">
          <thead><tr className="text-left border-b"><th className="p-2">Title</th><th className="p-2">Sales</th><th className="p-2">Profit JPY</th><th className="p-2">Margin%</th></tr></thead>
          <tbody>{bestSellers.map((item) => <tr key={item.title} className="border-b"><td className="p-2">{item.title}</td><td className="p-2">{item.sales_count}</td><td className="p-2">{item.total_profit_jpy}</td><td className="p-2">{item.avg_profit_margin.toFixed(2)}</td></tr>)}</tbody>
        </table>
      </section>
      <section>
        <h2 className="text-xl font-semibold mb-3">Category Analytics</h2>
        <table className="w-full bg-white rounded shadow text-sm">
          <thead><tr className="text-left border-b"><th className="p-2">Category</th><th className="p-2">Sales JPY</th><th className="p-2">Profit JPY</th><th className="p-2">Days to Sell</th></tr></thead>
          <tbody>{categories.map((item) => <tr key={item.category} className="border-b"><td className="p-2">{item.category}</td><td className="p-2">{item.total_sales_jpy}</td><td className="p-2">{item.total_profit_jpy}</td><td className="p-2">{item.avg_days_to_sell.toFixed(1)}</td></tr>)}</tbody>
        </table>
      </section>
    </div>
  )
}
