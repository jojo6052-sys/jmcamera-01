import { useState } from 'react'
import ProductAnalyticsPage from './pages/ProductAnalyticsPage'
import RecommendationsPage from './pages/RecommendationsPage'
import SearchKeywordsPage from './pages/SearchKeywordsPage'

type TabKey = 'analytics' | 'recommendations' | 'keywords'

export default function App() {
  const [tab, setTab] = useState<TabKey>('analytics')

  return (
    <div className="min-h-screen bg-slate-100 p-8 space-y-4">
      <h1 className="text-3xl font-bold">JM Camera Sourcing AI</h1>

      <div className="flex gap-2">
        <button className={`px-3 py-2 rounded ${tab === 'analytics' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('analytics')}>
          Product Analytics
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'recommendations' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('recommendations')}>
          Recommendations
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'keywords' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('keywords')}>
          Search Keywords
        </button>
      </div>

      {tab === 'analytics' && <ProductAnalyticsPage />}
      {tab === 'recommendations' && <RecommendationsPage />}
      {tab === 'keywords' && <SearchKeywordsPage />}
    </div>
  )
}
