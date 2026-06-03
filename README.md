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
