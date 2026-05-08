
import ProductAnalyticsPage from './pages/ProductAnalyticsPage'

const pages = ['Dashboard', 'Product Analytics', 'Search Keywords', 'Yahoo Search', 'Recommendations', 'Candidate Detail']


export default function App() {
  return (
    <div className="min-h-screen bg-slate-100 p-8">

      <h1 className="text-3xl font-bold mb-6">JM Camera Sourcing AI</h1>
      <ProductAnalyticsPage />

      <h1 className="text-3xl font-bold mb-6">JM Camera Sourcing AI (MVP Phase 1 Scaffold)</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {pages.map((page) => (
          <div key={page} className="rounded-lg bg-white p-4 shadow">
            <h2 className="font-semibold">{page}</h2>
            <p className="text-sm text-slate-600 mt-1">This page is reserved for upcoming PRs.</p>
          </div>
        ))}
      </div>

    </div>
  )
}
