# JM Camera Sourcing AI 進捗ロードマップ

このドキュメントは、完成していない部分を含めて「どこまでできていて、何が残っているか」を確認するための進捗表です。パーセンテージは、実装・検証・運用準備を含む目安です。

| 領域 | 進捗目安 | 状態 | できていること | 残っていること |
| --- | ---: | --- | --- | --- |
| Phase 1 Local MVP | 85% | 進行中 | CSVインポート、分析、検索KW、Yahoo fallback候補、推薦、フィードバック、競合調査、System Manual | 実データでの継続UX確認、Phase verification report定期保存、細かい導線改善 |
| Production Configuration | 35% | 外部待ち | Phase Status表示、eBay削除通知endpoint、Docker/agent接続ガイド | eBay Production keyset、外部公開HTTPS endpoint、verification token運用、本番secret管理 |
| External Data Acquisition | 45% | 進行中 | Yahoo live/fallback、eBay live/disabled、delay/timeout、保存HTMLインポート | Yahoo許可済み/安定導線、eBay Sold履歴の公式API/代替導線、レート制御強化、取得失敗時の観測性 |
| Scoring Intelligence | 40% | 計画中 | 推薦スコア再計算、S/A/B/C/NG、判断保存、CSV出力 | 返品・修理・クレーム履歴の重み付け、見送り理由分析、利益予測、フィードバック反映 |
| CI / Operations | 50% | 進行中 | dev_check、smoke_check、phase1_verify、Markdown report、Docker access check | GitHub Actions等での自動実行、Compose込みE2E、定期レポート、デプロイ先health監視 |

## 次に進める優先順

1. 実データで `phase1_verify` と画面UXを確認し、詰まる操作を小さく直す。
2. eBay Production credentials / compliance endpoint を設定し、Production Configurationを完了させる。
3. Yahoo/eBay取得の許可済み・安定導線を決め、live取得の運用ルールを固める。
4. フィードバック保存データを使って、推薦スコアの重み付け改善に着手する。

## 画面での確認

Frontendの `Progress` タブで、この進捗をカード形式で確認できます。`Phase Status` は現在の起動・設定状態、`Progress` は完成までの残タスクを見る画面として使い分けます。
