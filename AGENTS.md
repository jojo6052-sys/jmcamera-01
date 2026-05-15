
# AGENTS.md — JM Camera Sourcing AI

## 目的
本プロジェクトでは、複数エージェントで以下の自動ループを回す。  
**実装 → テスト → 失敗解析 → 修正 → 再テスト → PR作成**

---

## 共通原則（全エージェント必須）
1. 変更は必ず feature / fix ブランチで行う（main直コミット禁止）。
2. 1タスク1PR（スコープを小さく）。
3. 作業開始前に `main` を最新化する（`git pull origin main`）。
4. テスト失敗状態でコミットしない。
5. コンフリクトマーカー（`<<<<<<<` / `=======` / `>>>>>>>`）を残さない。
6. DRY / YAGNI / KISS を優先する。
7. 秘密情報（PAT/APIキー/.env）をコミット・共有しない。
8. 変更理由をPRに必ず記録する（Why/What/How）。

---

## ブランチ命名規則
- `feature/<scope>`
- `fix/<scope>`
- 例:
  - `feature/yahoo-real-fetch`
  - `fix/compose-port-8001`

---

## 役割分担（マルチエージェント）

### 1) Backend Agent
**責務**
- FastAPIルーター、サービス層、DB保存、Alembicマイグレーション
- 例外処理、ログ、入力バリデーション
- API契約（request/response）維持

**完了条件**
- APIが仕様どおりのレスポンスを返す
- DB整合性が保たれる
- backendテストが通る

### 2) Frontend Agent
**責務**
- React UI実装、API接続、画面状態管理
- エラー表示、ローディング表示、ユーザー導線改善
- 表示項目の整合（APIレスポンスとの一致）

**完了条件**
- 指定画面でデータ取得・表示ができる
- APIエラー時にUIが壊れない
- TypeScriptビルドが通る

### 3) QA / Review Agent
**責務**
- テスト追加・実行・失敗原因特定
- セキュリティ観点（入力値検証、危険実装）確認
- コード規約/重複/不要コードのレビュー

**完了条件**
- 必須テスト一式が通る
- 重大問題なしのレビュー結果を返す

---

## 実行コマンド（標準）

### 環境起動
```bash
cp .env.example .env
docker compose up -d --build
Backend
docker compose exec backend pytest -q
docker compose exec backend python -m compileall app
Frontend
docker compose exec frontend npm run build
Health Check（jmcamera-01は8001）
curl -i http://localhost:8001/health
curl -i http://localhost:8001/api/health
Docker / ポート方針
backend container内部ポート: 8000

host公開ポート: 8001:8000

frontend: 5173

他プロジェクトとの競合回避を優先する

PRテンプレ（必須）
PR本文は以下の順で記載:

目的（Why）

変更内容（What）

テスト結果（How verified）

既知の制約 / 次PR課題（Follow-up）

マージ前チェックリスト（必須）
 git status が clean

 git diff --check が空

 backendテスト通過

 frontend build成功

 /health と /api/health が 200

 README更新（必要時）

 コンフリクトマーカーなし

 .env や秘密情報が差分に含まれていない

Phase 1 実装優先順
CSVインポート

分析API/画面

Yahoo候補取得と保存

推薦スコア

フィードバック保存

Yahoo取得の注意（MVP）
過剰アクセス禁止（ランダム待機）

失敗時もAPIを落とさない

ログイン必須情報は扱わない

スクレイピング実装はサービス層へ分離（将来差し替え可能）

セキュリティ注意
PATは会話/コード/ログに貼らない

.env はコミット禁止

外部入力は必ずバリデーションする
