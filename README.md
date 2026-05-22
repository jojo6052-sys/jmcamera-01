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
