# AGENTS.md — JM Camera Sourcing AI

## 目的
本プロジェクトでは、複数エージェントで以下の自動ループを回す。  
**実装 → テスト → 失敗解析 → 修正 → 再テスト → PR作成**

---

## 共通原則（全エージェント必須）
1. 変更は必ず feature ブランチで行う（main 直コミット禁止）。
2. 1タスク1PR（スコープを小さく）。
3. 変更前に `git pull origin main` を実施し、最新化してから作業開始。
4. テストが失敗した状態でコミットしない。
5. コンフリクトマーカー（`<<<<<<<` 等）を残さない。
6. DRY / YAGNI / KISS を優先。
7. セキュリティ上、秘密情報（PAT/APIキー）をコミット・共有しない。

---

## ブランチ命名規則
- `feature/<scope>`
- `fix/<scope>`
- 例: `feature/yahoo-real-fetch`, `fix/compose-port-8001`

---

## 役割分担

### 1) Backend Agent
責務:
- FastAPI ルーター、サービス層、DB保存、Alembicマイグレーション
- 例外処理、ログ、入力バリデーション

完了条件:
- APIが仕様どおりレスポンスを返す
- DB整合性が保たれる
- backendテストが通る

---

### 2) Frontend Agent
責務:
- React UI実装、API接続、画面状態管理
- エラー表示、ローディング表示、ユーザー導線改善

完了条件:
- 指定画面でデータ取得・表示ができる
- APIエラー時にUIが壊れない
- 型エラーがない（TypeScript）

---

### 3) QA / Review Agent
責務:
- テスト追加・実行・失敗原因特定
- セキュリティ観点（入力値検証、危険な実装）確認
- コード規約/重複/不要コードのレビュー

完了条件:
- 必須テスト一式が通る
- 重大問題なしのレビュー結果を返す

---

## 実行コマンド（標準）

### 環境起動
```bash
cp .env.example .env
docker compose up -d --build
