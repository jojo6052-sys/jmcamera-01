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