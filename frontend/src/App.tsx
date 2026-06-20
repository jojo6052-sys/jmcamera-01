import { useState } from 'react'
import ProductAnalyticsPage from './pages/ProductAnalyticsPage'
import RecommendationsPage from './pages/RecommendationsPage'
import CompetitorResearchPage from './pages/CompetitorResearchPage'
import SearchKeywordsPage from './pages/SearchKeywordsPage'
import PhaseStatusPage from './pages/PhaseStatusPage'
import SystemGuidePage from './pages/SystemGuidePage'
import ProgressRoadmapPage from './pages/ProgressRoadmapPage'

type TabKey = 'status' | 'guide' | 'progress' | 'analytics' | 'recommendations' | 'keywords' | 'competitors'

const galleryItems = [
  {
    src: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=900&q=80',
    alt: '夕暮れの東京の路地',
    caption: '夕暮れ、音が少し遠のく路地。',
  },
  {
    src: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80',
    alt: '木製テーブルの上のクラシックカメラ',
    caption: '古いカメラが教えてくれる、待つ楽しみ。',
  },
  {
    src: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=900&q=80',
    alt: '静かな日本の街並み',
    caption: '観光地のすぐ隣にある、静かな東京。',
  },
]

const voices = [
  '朝のコーヒーを飲みながら読むと、週末の過ごし方が少し丁寧になります。東京に住んでいても知らない場所が多いと気づきました。',
  '宿泊先から歩ける小さな路地の紹介が心に残りました。旅程を詰め込まない旅の良さを思い出せます。',
  'フィルムカメラの話が懐かしく、写真を撮る時間そのものを楽しめるようになりました。',
]

function NewsletterForm({ id }: { id: string }) {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmedEmail = email.trim()

    if (!trimmedEmail) {
      setMessage('メールアドレスを入力してください。')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setMessage('有効なメールアドレスを入力してください。')
      return
    }

    setMessage('ご登録ありがとうございます。次回のレターをお楽しみに。')
    setEmail('')
  }

  return (
    <div className="min-h-screen bg-slate-100 p-8 space-y-4">
      <h1 className="text-3xl font-bold">JM Camera Sourcing AI</h1>

      <div className="flex flex-wrap gap-2">
        <button className={`px-3 py-2 rounded ${tab === 'status' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('status')}>
          Phase Status
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'guide' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('guide')}>
          System Manual
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'progress' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('progress')}>
          Progress
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'analytics' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('analytics')}>
          Product Analytics
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'recommendations' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('recommendations')}>
          Recommendations
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'keywords' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('keywords')}>
          Search Keywords
        </button>
        <button className={`px-3 py-2 rounded ${tab === 'competitors' ? 'bg-slate-800 text-white' : 'bg-white'}`} onClick={() => setTab('competitors')}>
          Competitor Research
        </button>
      </div>

      {tab === 'status' && <PhaseStatusPage onOpenGuide={() => setTab('guide')} />}
      {tab === 'guide' && <SystemGuidePage />}
      {tab === 'progress' && <ProgressRoadmapPage />}
      {tab === 'analytics' && <ProductAnalyticsPage />}
      {tab === 'recommendations' && <RecommendationsPage />}
      {tab === 'keywords' && <SearchKeywordsPage />}
      {tab === 'competitors' && <CompetitorResearchPage />}
    </div>
  )
}
