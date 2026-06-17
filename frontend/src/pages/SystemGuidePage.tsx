const workflowSteps = [
  {
    title: '1. Phase Statusで起動状態を確認',
    body: 'Docker起動後にDB接続、主要テーブル件数、ローカルMVP readiness、Production向け未設定項目を確認します。',
  },
  {
    title: '2. CSVを取り込んで販売傾向を分析',
    body: '過去販売CSVをProduct Analyticsに取り込み、商品別・カテゴリ別の売上、利益、回転日数を見ます。',
  },
  {
    title: '3. Search Keywordsから候補を集める',
    body: '仕入れたいブランド・モデル名を検索KWとして登録し、Yahoo候補取得条件や除外ワードを指定します。',
  },
  {
    title: '4. Recommendationsで判断を保存',
    body: '候補をスコアリングし、仕入れ・要確認・見送りの判断をフィードバックとして蓄積します。',
  },
  {
    title: '5. Competitor Researchで次のKWを作る',
    body: 'eBayライバルセラーの出品中/Sold商品を調査し、頻出語や推奨検索KWを次の候補取得につなげます。',
  },
]

const currentScope = [
  'ローカルMVPではCSVインポート、分析、検索KW、Yahoo候補、推薦スコア、フィードバック、ライバル分析を一通り確認できます。',
  'eBay API credentialsやMarketplace Account Deletion endpointはProduction向け設定です。未設定でもローカルMVPの動作確認は継続できます。',
  'Yahoo取得はデフォルトfallbackで外部サイトへアクセスしません。実取得検証時のみ明示的にliveへ切り替えます。',
]

const futureRoadmap = [
  {
    title: '外部連携のProduction化',
    body: 'eBay Production keyset、削除通知endpoint、公式/許可済みデータ取得経路を整え、ローカル検証から実運用へ移行します。',
  },
  {
    title: '推薦スコアの高度化',
    body: '過去販売実績、返品・修理・クレーム履歴、ユーザーの見送り理由を使い、利益見込みとリスクをより精密に評価します。',
  },
  {
    title: '継続運用とCIの整備',
    body: 'backend pytest、frontend build、smoke check、Phase verification reportをCIに組み込み、PRごとに品質を確認します。',
  },
]

export default function SystemGuidePage() {
  return (
    <div className="space-y-4">
      <section className="bg-white rounded shadow p-5 space-y-2">
        <p className="text-sm font-semibold text-slate-500">System Manual</p>
        <h2 className="text-2xl font-bold">JM Camera Sourcing AI の全体像</h2>
        <p className="text-slate-700 leading-7">
          JM Camera Sourcing AIは、カメラ商品の仕入れ判断を、過去販売データ・候補取得・競合調査・推薦スコア・人間のフィードバックで回すためのPhase 1 MVPです。
          まずはローカル環境で一連の導線を安定して確認し、将来的にはeBay/Yahoo連携や推薦ロジックを強化して実運用できる仕入れ支援システムへ育てます。
        </p>
      </section>

      <section className="grid lg:grid-cols-4 gap-3">
        <div className="bg-white rounded shadow p-4">
          <div className="text-xs text-slate-500">Backend</div>
          <div className="font-semibold">FastAPI</div>
          <p className="text-sm text-slate-600 mt-1">API、DB保存、分析、外部取得サービスを担当します。</p>
        </div>
        <div className="bg-white rounded shadow p-4">
          <div className="text-xs text-slate-500">Frontend</div>
          <div className="font-semibold">React + Vite</div>
          <p className="text-sm text-slate-600 mt-1">Phase Status、分析、推薦、KW管理、競合調査を操作します。</p>
        </div>
        <div className="bg-white rounded shadow p-4">
          <div className="text-xs text-slate-500">Database</div>
          <div className="font-semibold">PostgreSQL</div>
          <p className="text-sm text-slate-600 mt-1">商品、候補、スコア、フィードバック、競合データを保存します。</p>
        </div>
        <div className="bg-white rounded shadow p-4">
          <div className="text-xs text-slate-500">Cache / Jobs</div>
          <div className="font-semibold">Redis</div>
          <p className="text-sm text-slate-600 mt-1">将来の非同期処理やキャッシュ基盤として使います。</p>
        </div>
      </section>

      <section className="bg-white rounded shadow p-5">
        <h3 className="text-lg font-semibold mb-3">大まかな使い方</h3>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
          {workflowSteps.map((step) => (
            <div key={step.title} className="border border-slate-200 rounded p-3">
              <h4 className="font-semibold">{step.title}</h4>
              <p className="text-sm text-slate-600 mt-1 leading-6">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="bg-white rounded shadow p-5">
          <h3 className="text-lg font-semibold mb-3">現在のPhase 1 MVPの見方</h3>
          <ul className="list-disc pl-5 space-y-2 text-sm text-slate-700 leading-6">
            {currentScope.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded shadow p-5">
          <h3 className="text-lg font-semibold mb-3">将来の形</h3>
          <div className="space-y-3">
            {futureRoadmap.map((item) => (
              <div key={item.title}>
                <h4 className="font-semibold">{item.title}</h4>
                <p className="text-sm text-slate-600 leading-6">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-slate-900 text-white rounded shadow p-5">
        <h3 className="text-lg font-semibold">次に確認するコマンド</h3>
        <p className="text-sm text-slate-200 mt-1">Compose起動後は、以下でhealth、画面、write smoke flowをまとめて確認できます。</p>
        <pre className="mt-3 overflow-x-auto rounded bg-black/40 p-3 text-sm"><code>{'python scripts/phase1_verify.py --backend-base-url http://localhost:8001 --frontend-url http://localhost:5173 --report-file reports/phase1-verification.md'}</code></pre>
      </section>
    </div>
  )
}
