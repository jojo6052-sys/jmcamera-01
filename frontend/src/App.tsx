import { useState } from 'react'
import ProductAnalyticsPage from './pages/ProductAnalyticsPage'
import RecommendationsPage from './pages/RecommendationsPage'
import CompetitorResearchPage from './pages/CompetitorResearchPage'
import SearchKeywordsPage from './pages/SearchKeywordsPage'
import PhaseStatusPage from './pages/PhaseStatusPage'
import SystemGuidePage from './pages/SystemGuidePage'
import ProgressRoadmapPage from './pages/ProgressRoadmapPage'

type TabKey = 'status' | 'guide' | 'progress' | 'analytics' | 'recommendations' | 'keywords' | 'competitors'

const tabs: { key: TabKey; label: string; description: string }[] = [
  { key: 'status', label: 'Phase Status', description: 'MVPの準備状況' },
  { key: 'guide', label: 'System Manual', description: '運用ガイド' },
  { key: 'progress', label: 'Progress', description: '進捗ロードマップ' },
  { key: 'analytics', label: 'Product Analytics', description: '商品分析' },
  { key: 'recommendations', label: 'Recommendations', description: '推薦スコア' },
  { key: 'keywords', label: 'Search Keywords', description: '検索キーワード' },
  { key: 'competitors', label: 'Competitor Research', description: '競合調査' },
]

export default function App() {
  const [tab, setTab] = useState<TabKey>('status')
  const activeTab = tabs.find((item) => item.key === tab) ?? tabs[0]

  return (
    <div className="app-shell">
      <header className="app-hero">
        <div>
          <p className="app-kicker">JM Camera Sourcing AI</p>
          <h1 className="app-title">仕入れ判断ダッシュボード</h1>
          <p className="app-lead">Phase 1 MVPの状態確認、商品分析、候補取得、推薦判断をひとつの画面から確認できます。</p>
        </div>
        <div className="app-status-card" aria-label="現在の表示タブ">
          <span>Current View</span>
          <strong>{activeTab.label}</strong>
          <small>{activeTab.description}</small>
        </div>
      </header>

      <nav className="tab-nav" aria-label="主要機能">
        {tabs.map((item) => (
          <button className={`tab-button ${tab === item.key ? 'is-active' : ''}`} key={item.key} onClick={() => setTab(item.key)} type="button">
            <span>{item.label}</span>
            <small>{item.description}</small>
          </button>
        ))}
      </nav>

      <main className="app-content">
        {tab === 'status' && <PhaseStatusPage onOpenGuide={() => setTab('guide')} />}
        {tab === 'guide' && <SystemGuidePage />}
        {tab === 'progress' && <ProgressRoadmapPage />}
        {tab === 'analytics' && <ProductAnalyticsPage />}
        {tab === 'recommendations' && <RecommendationsPage />}
        {tab === 'keywords' && <SearchKeywordsPage />}
        {tab === 'competitors' && <CompetitorResearchPage />}
      </main>
    </div>
  )
}
