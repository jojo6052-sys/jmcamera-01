import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'
import type { BestSellerItem, CategoryAnalyticsItem } from '../types/analytics'

export default function ProductAnalyticsPage() {
  const [bestSellers, setBestSellers] = useState<BestSellerItem[]>([])
  const [categories, setCategories] = useState<CategoryAnalyticsItem[]>([])

  useEffect(() => {
    apiGet<BestSellerItem[]>('/api/analytics/best-sellers').then(setBestSellers).catch(() => setBestSellers([]))
    apiGet<CategoryAnalyticsItem[]>('/api/analytics/categories').then(setCategories).catch(() => setCategories([]))
  }, [])

  return (
    <div className="space-y-8">
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
