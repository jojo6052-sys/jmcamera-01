type ProgressArea = {
  title: string
  percent: number
  status: 'done' | 'in-progress' | 'blocked' | 'planned'
  summary: string
  done: string[]
  remaining: string[]
}

const progressAreas: ProgressArea[] = [
  {
    title: 'Phase 1 Local MVP',
    percent: 85,
    status: 'in-progress',
    summary: 'ローカル環境で仕入れ判断の一連の流れを確認できる状態です。',
    done: ['CSVインポート', 'Product Analytics', 'Search Keywords', 'Yahoo候補fallback取得', 'Recommendations', 'フィードバック保存', 'Competitor Research MVP', 'System Manual'],
    remaining: ['実データでの継続UX確認', 'Phase verification reportの定期保存', '細かい画面導線改善'],
  },
  {
    title: 'Production Configuration',
    percent: 35,
    status: 'blocked',
    summary: '本番外部連携に必要なeBay設定と公開endpoint準備が残っています。',
    done: ['設定状態をPhase Statusへ表示', 'Marketplace Account Deletion endpoint実装', 'Docker/agent接続ガイド'],
    remaining: ['eBay Production keyset設定', '外部公開HTTPS endpoint設定', 'verification token運用', '本番secret管理'],
  },
  {
    title: 'External Data Acquisition',
    percent: 45,
    status: 'in-progress',
    summary: 'MVPでは安全なfallback/disabled設定を優先し、live取得は明示的に切り替える設計です。',
    done: ['Yahoo fallback/live切替', 'eBay public fetch live/disabled切替', 'ランダムdelayとtimeout設定', '保存HTMLインポート導線'],
    remaining: ['Yahoo取得の許可済み/安定導線', 'eBay Sold履歴の公式APIまたは代替導線', 'レート制御の強化', '取得失敗時の観測性向上'],
  },
  {
    title: 'Scoring Intelligence',
    percent: 40,
    status: 'planned',
    summary: '推薦スコアと人間の判断保存はありますが、学習・高度なリスク評価は今後の拡張です。',
    done: ['推薦スコア再計算', 'S/A/B/C/NGランク表示', '仕入れ/要確認/見送り保存', 'CSV出力'],
    remaining: ['返品・修理・クレーム履歴の重み付け', '見送り理由の分析', '利益予測モデル', 'ユーザーフィードバック反映'],
  },
  {
    title: 'CI / Operations',
    percent: 50,
    status: 'in-progress',
    summary: 'ローカル検証スクリプトは整っています。次はCIと運用レポートへの組み込みです。',
    done: ['dev_check', 'smoke_check', 'phase1_verify', 'Markdown report出力', 'Docker access check'],
    remaining: ['GitHub Actions等での自動実行', 'Compose込みE2E検証', '定期レポート保存', 'デプロイ先のhealth監視'],
  },
]

const statusStyles: Record<ProgressArea['status'], string> = {
  done: 'bg-emerald-100 text-emerald-800',
  'in-progress': 'bg-sky-100 text-sky-800',
  blocked: 'bg-amber-100 text-amber-800',
  planned: 'bg-slate-100 text-slate-800',
}

const statusLabels: Record<ProgressArea['status'], string> = {
  done: '完了',
  'in-progress': '進行中',
  blocked: '外部待ち',
  planned: '計画中',
}

const overallPercent = Math.round(progressAreas.reduce((sum, area) => sum + area.percent, 0) / progressAreas.length)

export default function ProgressRoadmapPage() {
  return (
    <div className="space-y-4">
      <section className="bg-white rounded shadow p-5 space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-500">Progress Roadmap</p>
            <h2 className="text-2xl font-bold">未完成部分と進捗</h2>
            <p className="text-slate-700 leading-7 mt-2">
              現時点の進捗を「ローカルMVP」「本番設定」「外部データ取得」「推薦ロジック」「運用/CI」に分けて見える化しています。
              パーセンテージは実装・検証・運用準備を含む目安です。
            </p>
          </div>
          <div className="bg-slate-900 text-white rounded p-4 min-w-40 text-center">
            <div className="text-xs text-slate-300">Overall</div>
            <div className="text-3xl font-bold">{overallPercent}%</div>
            <div className="text-xs text-slate-300">実運用完成までの目安</div>
          </div>
        </div>
      </section>

      <section className="grid gap-4">
        {progressAreas.map((area) => (
          <article key={area.title} className="bg-white rounded shadow p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-lg font-semibold">{area.title}</h3>
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${statusStyles[area.status]}`}>{statusLabels[area.status]}</span>
                </div>
                <p className="text-sm text-slate-600 mt-1">{area.summary}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">{area.percent}%</div>
                <div className="text-xs text-slate-500">progress</div>
              </div>
            </div>

            <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full rounded-full bg-slate-800" style={{ width: `${area.percent}%` }} />
            </div>

            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-semibold text-emerald-800 mb-2">できていること</h4>
                <ul className="list-disc pl-5 space-y-1 text-slate-700">
                  {area.done.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-amber-800 mb-2">残っていること</h4>
                <ul className="list-disc pl-5 space-y-1 text-slate-700">
                  {area.remaining.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="bg-white rounded shadow p-5">
        <h3 className="text-lg font-semibold mb-2">次に進める優先順</h3>
        <ol className="list-decimal pl-5 space-y-2 text-sm text-slate-700 leading-6">
          <li>実データで `phase1_verify` と画面UXを確認し、詰まる操作を小さく直す。</li>
          <li>eBay Production credentials / compliance endpoint を設定し、Production Configurationを完了させる。</li>
          <li>Yahoo/eBay取得の許可済み・安定導線を決め、live取得の運用ルールを固める。</li>
          <li>フィードバック保存データを使って、推薦スコアの重み付け改善に着手する。</li>
        </ol>
      </section>
    </div>
  )
}
