# JM Camera Sourcing AI システムマニュアル

JM Camera Sourcing AI は、カメラ商品の仕入れ判断を支援するための Phase 1 MVP です。過去販売CSV、Yahoo候補、eBay競合調査、推薦スコア、ユーザーフィードバックを1つのローカルWebアプリでつなぎ、仕入れ判断の再現性を高めます。

## システムの目的

1. 過去販売実績から、売れ筋・利益率・回転日数を把握する。
2. 仕入れ候補を探す検索キーワードを管理する。
3. Yahoo候補を取得・保存し、価格条件や除外ワードで絞り込む。
4. 推薦スコアを計算し、仕入れ・要確認・見送りの判断を保存する。
5. eBayライバルセラーの出品/Sold情報から、次の検索キーワードを作る。

## 構成

| 領域 | 技術 | 役割 |
| --- | --- | --- |
| Backend | FastAPI | API、DB保存、分析、外部取得サービス |
| Frontend | React + Vite + Tailwind | 画面操作、候補確認、判断保存 |
| Database | PostgreSQL | 商品、候補、スコア、フィードバック、競合データ保存 |
| Cache / Jobs | Redis | 将来の非同期処理・キャッシュ基盤 |

## ポート住み分け

- JM Camera Sourcing AI frontend: `http://localhost:5173`
- 別プロジェクトのランディングページ: `http://localhost:5174`

仕入れシステム側はDocker Composeの `5173:5173` とVite `strictPort` で5173に固定しています。5173が使われている場合は自動的に5174へずれず、競合として検知します。

## 大まかな使い方

### 1. 起動と状態確認

```bash
cp .env.example .env
docker compose up -d --build
curl -i http://localhost:8001/health
curl -i http://localhost:8001/api/health
curl -s http://localhost:8001/api/phase/status | python -m json.tool
```

Frontend は `http://localhost:5173` で開きます。最初は `Phase Status` タブで、DB接続、主要データ件数、ローカルMVP readiness、Production向け未設定項目を確認します。

### 2. CSVインポートと分析

`Product Analytics` タブで販売CSVを取り込みます。取り込み後、Best Sellers と Category Analytics で商品別・カテゴリ別の売上、利益、利益率、回転日数を確認します。

### 3. 検索キーワード管理とYahoo候補取得

`Search Keywords` タブでブランド名やモデル名を登録します。取得件数、価格条件、除外ワードを指定して候補取得を実行し、保存された候補を `Recommendations` タブで確認します。

MVPの安定検証では `YAHOO_FETCH_MODE=fallback` がデフォルトです。実Yahoo検索ページ取得を試す場合のみ `.env` で `YAHOO_FETCH_MODE=live` を明示します。

### 4. 推薦とフィードバック

`Recommendations` タブで候補を絞り込み、`Score` で推薦スコアを再計算します。その後、`仕入れ` / `要確認` / `見送り` を保存します。これにより、人間の判断が次の改善材料として蓄積されます。

### 5. 競合調査

`Competitor Research` タブでeBayセラーURLを投入し、出品中商品やSold Itemsの代替インポートを確認します。頻出語や推奨検索KWを `Search Keywords` に保存し、次の候補取得につなげます。

## 現在のPhase 1 MVPの見方

- `core_ready=true`: CSVインポート、分析、検索KW、Yahoo候補、推薦スコア、フィードバック、ライバル分析のローカルMVP導線が確認可能です。
- `status=ready_with_configuration_pending`: ローカルMVPは動作可能ですが、eBay API credentials や Marketplace Account Deletion endpoint などProduction向け設定が未完了です。
- eBay / Yahoo の外部取得は、過剰アクセスを避けるため設定値でlive/fallback/disabled、delay、timeoutを制御します。

## 動作確認

```bash
python scripts/smoke_check.py --base-url http://localhost:8001
python scripts/smoke_check.py --base-url http://localhost:8001 --include-write-checks
python scripts/phase1_verify.py --backend-base-url http://localhost:8001 --frontend-url http://localhost:5173 --report-file reports/phase1-verification.md
```

PR前のローカル確認は以下を使います。

```bash
scripts/dev_check.sh
```

Docker権限まで含めて確認する場合は以下です。

```bash
scripts/check_docker_access.sh --runtime-smoke
```

## 将来のロードマップ

1. **Production向け外部連携**: eBay Production keyset、Marketplace Account Deletion endpoint、公式/許可済みデータ取得経路を整備する。
2. **取得処理の安定化**: Yahoo/eBay取得をレート制御、失敗時fallback、保存HTMLインポート、公式API優先の設計で運用可能にする。
3. **推薦スコアの高度化**: 過去利益、返品、修理、クレーム、見送り理由を反映し、期待利益とリスクをより精密に評価する。
4. **CI/検証レポート**: backend pytest、frontend build、smoke check、Phase verification reportをPRごとに自動化する。
5. **実運用画面の改善**: 仕入れ担当者が毎日見るダッシュボード、アラート、CSV/レポート出力を拡張する。

## 関連画面

Frontendには、この内容を読むための `System Manual` タブを追加しています。Phase Statusで状態確認後、System Manualで全体の流れと将来像を確認してください。
