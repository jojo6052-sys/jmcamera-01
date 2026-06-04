# JM Camera Sourcing AI (MVP Scaffold)

このPRは Phase 1 の初期セットアップです（#20 の最初のタスク）。

## 含まれるもの
- Docker Compose（backend / frontend / PostgreSQL / Redis）
- FastAPI 起動 + `/health`
- PostgreSQL 接続設定（SQLAlchemy）
- MVP用テーブルの SQLAlchemy モデル定義
- Alembic 設定 + 初期マイグレーション
- React + Vite + TypeScript + Tailwind の初期起動
- `.env.example`

## ディレクトリ構成
- `backend/` FastAPI + SQLAlchemy + Alembic
- `frontend/` React + Vite + Tailwind

## セットアップ
```bash
cp .env.example .env
docker compose up --build
```

## 動作確認
- Backend health: `http://localhost:8001/health`
- API health: `http://localhost:8001/api/health`
- Frontend: `http://localhost:5173`

## Alembic
初期マイグレーション適用（backend コンテナ内）:
```bash
docker compose exec backend alembic upgrade head
```

## 次PRで実装予定
- CSV インポートAPI
- 分析API
- 分析画面
- ヤフオク検索サービス / 候補保存 / 推薦スコア / フィードバック


## Dockerが無い環境でのローカル検証
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=. pytest -q
```

> 注意: PostgreSQL/Redis連携やAlembicの実DB適用は Docker またはローカルDB が必要です。

## Phase 1 - PR2 追加機能
- `POST /api/import/products`: CSVから`products`へ取り込み
- `GET /api/analytics/best-sellers`: 商品別の販売件数・売上・利益・利益率・平均販売日数
- `GET /api/analytics/categories`: カテゴリ別の売上・利益・利益率・回転日数
- Frontendは Product Analytics テーブルをAPI連携で表示

### CSVサンプルヘッダー
```csv
es_number,title,normalized_title,brand,model,category,mount,condition_rank,purchase_price_jpy,sale_price_usd,sale_price_jpy,gross_profit_jpy,final_profit_jpy,profit_margin,purchased_at,listed_at,sold_at,days_to_sell,sales_channel,buyer_country,returned,complaint,repair_required,seller_id,source_platform,source_url,notes
```

## Phase 1 - PR3 追加機能（MVP版）
- `GET/POST/PUT/DELETE /api/search-keywords`
- `POST /api/yahoo/search`（MVPでは安全なダミー候補生成で保存、後続PRでスクレイパ差し替え）
- `GET /api/candidates`
- `GET /api/candidates/{id}`


## Phase 1 - PR4 追加機能
- `POST /api/candidates/{id}/feedback`: 仕入れ判断フィードバック保存

- `POST /api/candidates/{id}/score`: 推薦スコアを再計算して保存
- `GET /api/candidates` は `rank` / `min_score` フィルタに対応

- `GET /api/candidates/export.csv`: 候補一覧をCSVダウンロード（既存フィルタ適用）
- `POST /api/yahoo/search` は `min_price` / `max_price` / `exclude_words` に対応

## UX検証チェックポイント（2026-06-01）
現状は、以下の流れをブラウザ上で一通り確認できる区切りです。

### 1. 起動
```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend health: http://localhost:8001/health
- API health: http://localhost:8001/api/health

### 2. Search Keywordsで候補取得
1. `Search Keywords` タブを開く。
2. `keyword` に例として `Canon EOS 5D` を入力し、必要に応じて category / brand / priority を入力する。
3. `追加` を押してキーワードを登録する。
4. `ヤフオク候補取得条件` で取得件数、最低価格、最高価格、除外ワードを設定する。
5. 登録済みキーワード行の `候補取得` を押す。
6. 成功メッセージが表示されたら `Recommendations` タブへ移動する。

### 3. Recommendationsで推薦確認
1. `Recommendations` タブでキーワード、ランク、最小スコア、上限価格を指定して `検索` する。
2. 候補行の `Score` を押して推薦スコアを計算する。
3. 必要に応じて `仕入れ` / `要確認` / `見送り` を押して判断を保存する。
4. `CSV出力` で現在の条件に一致する候補一覧をダウンロードする。

### 4. Product Analytics確認
1. `Product Analytics` タブを開く。
2. 手元にCSVが無い場合は `サンプルCSVダウンロード` を押して検証用CSVを保存する。
3. ファイル選択でCSVを選び、`CSVインポート` を押す。
4. 成功メッセージが表示されたら Best Sellers と Category Analytics が更新されていることを確認する。
5. 必要に応じて `再読み込み` を押して最新の分析結果を取得する。

APIから直接投入する場合は以下でも実行できます。

```bash
curl -X POST http://localhost:8001/api/import/products \
  -F "file=@path/to/products.csv"
```

CSVヘッダー例は「CSVサンプルヘッダー」を参照してください。

### 検証時に見てほしいポイント
- 初回ユーザーが迷わず「キーワード追加 → 候補取得 → 推薦スコア → 判断保存」まで進めるか。
- 価格条件・除外ワードの意味が画面だけで理解できるか。
- RecommendationsのフィルタとCSV出力が期待どおりか。
- 表示文言、ボタン配置、テーブル項目に不足がないか。

## Competitor Research（eBayセラー分析 MVP）
- `POST /api/competitors/analyze`: eBayセラーURLから出品中商品 / Sold Items を取得して `competitor_sellers` / `competitor_items` に保存
- `GET /api/competitors`: 保存済みライバルセラーの件数・平均価格サマリを取得
- `GET /api/competitors/{seller_id}/items`: ライバル商品の一覧を status / keyword で絞り込み
- `GET /api/competitors/{seller_id}/export.csv`: 現在のライバル商品フィルタをCSV出力
- Frontendは `Competitor Research` タブでセラーURL投入、出品中 / Sold Items の取り込み、保存済みセラー比較、商品一覧確認、CSV出力に対応

### eBayセラーURL例
```text
https://www.ebay.com/str/example-seller
https://www.ebay.com/usr/example-seller
https://www.ebay.com/sch/i.html?_ssn=example-seller
```

> 注意: MVPではeBayの公開検索ページを控えめに取得して解析します。eBayが自動取得を403 Forbiddenで拒否した場合は `fetch_status=blocked`、その他のページ構造変更・アクセス制限時は `fetch_status=failed` としてセラー情報だけを残し、API全体は落とさない設計です。本格運用ではeBay公式API連携やレート制御を追加する予定です。

## eBay Marketplace Account Deletion endpoint
Production keysetのcompliance対応用に、以下のendpointを用意しています。

- `GET /api/ebay/marketplace-account-deletion`: eBayの`challenge_code`検証に対して`challengeResponse`を返す
- `POST /api/ebay/marketplace-account-deletion`: account deletion通知を受け取り、payload内のusernameと一致する保存済みcompetitor sellerを削除

`.env`には、eBay Developer Portalに入力する値と完全一致するHTTPS URLとverification tokenを設定してください。

```env
EBAY_MARKETPLACE_DELETION_VERIFICATION_TOKEN=任意の安全な検証トークン
EBAY_MARKETPLACE_DELETION_ENDPOINT_URL=https://your-domain.example/api/ebay/marketplace-account-deletion
```

> eBay Developer Portalに登録するendpointは外部から到達可能なHTTPS URLである必要があります。`localhost`やDocker内部URLは登録できません。

## eBay Browse API連携（出品中商品の安定取得）
Production keyset取得後は、以下を `.env` に設定するとCompetitor Researchの「出品中」取得でeBay Browse APIを優先します。

```env
EBAY_CLIENT_ID=ProductionのApp ID / Client ID
EBAY_CLIENT_SECRET=ProductionのCert ID / Client Secret
EBAY_MARKETPLACE_ID=EBAY_US
```

- `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` が設定されている場合、`include_active=true` の出品中商品は `GET https://api.ebay.com/buy/browse/v1/item_summary/search` を `filter=sellers:{seller_username}` で呼び出します。
- `include_sold=true` のSold Itemsは、現時点では引き続き公開ページ解析のfallbackです。公式APIでSold履歴を安定取得するには追加API権限または代替インポート導線が必要です。
- `EBAY_CLIENT_SECRET` は秘密情報なので、チャット・PR・Gitには貼らず、ローカル `.env` やデプロイ先のSecretにのみ保存してください。

## eBay保存HTMLインポート（Sold Items代替導線）
eBay側の403ブロックや公式API権限不足でSold Itemsを直接取得できない場合、ブラウザで保存したHTMLを取り込めます。

1. eBayでライバルセラーのSold Items画面を開く。
2. ブラウザでページをHTMLとして保存する。
3. `Competitor Research` タブで同じセラーURLを入力する。
4. `保存HTMLから取り込み` で `Sold Items HTML` を選び、保存したHTMLをアップロードする。

APIから直接取り込む場合:

```bash
curl -X POST http://localhost:8001/api/competitors/import-html \
  -F "seller_url=https://www.ebay.com/str/example-seller" \
  -F "item_status=sold" \
  -F "file=@sold-items.html"
```

> 保存HTMLインポートは、画面で見えている範囲をリサーチDBに取り込むためのMVP代替導線です。大量取得や継続監視はeBay公式API/許可された連携方式を優先してください。
