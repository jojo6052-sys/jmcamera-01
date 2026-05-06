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
- Backend health: `http://localhost:8000/health`
- API health: `http://localhost:8000/api/health`
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
