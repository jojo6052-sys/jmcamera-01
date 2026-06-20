# 推薦スコア学習・補正ルール

推薦スコアは、価格・利益見込み・説明欄リスク・写真情報・出品者評価・手動補正ルールを組み合わせて計算します。

## 評価に入る観点

- **販売写真**: 写真枚数、写真なし、placeholder/noimage/blurなど低品質を示すURL文字列をリスクとして扱います。将来は画像解析モデルでカビ、曇り、傷、付属品不足を判定する予定です。
- **販売説明欄**: `ジャンク`、`不動`、`カビ`、`水没`、`動作未確認` などをリスク加点し、`動作品`、`防湿庫`、`整備済` などをプラス評価します。
- **販売者評価**: seller ratingが低い場合はリスクを上げ、特に低い場合はNGにします。
- **仕入れ実績・知見**: `scoring_rules` にあとから補正ルールを追加し、タイトル/説明欄/販売者IDに一致した候補へスコア補正や上限入札率補正を適用します。

## 補正ルールAPI

### 一覧

```bash
curl -s http://localhost:8001/api/scoring-rules | python -m json.tool
```

### 追加

```bash
curl -X POST http://localhost:8001/api/scoring-rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nikon F3 整備済みは強め",
    "match_type": "keyword",
    "pattern": "Nikon F3",
    "score_adjustment": 8,
    "max_bid_adjustment_pct": 5,
    "risk_level": "positive",
    "reason": "過去実績上、整備済みは回転が早い"
  }'
```

### 危険販売者をNG寄りにする例

```bash
curl -X POST http://localhost:8001/api/scoring-rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "説明相違が多い販売者",
    "match_type": "seller_id",
    "pattern": "risky-seller",
    "score_adjustment": -50,
    "max_bid_adjustment_pct": -50,
    "risk_level": "critical",
    "reason": "過去に説明相違が多いため仕入れ対象外"
  }'
```

`risk_level=critical` のルールに一致した候補は `NG` になります。ルール追加後、候補の `Score` または一括 `Score` を再実行すると補正が反映されます。

## 今後の拡張

1. 実際の販売写真を画像解析し、カビ・曇り・傷・付属品の有無を判定する。
2. フィードバック/仕入れ実績から、利益が出やすいブランド・モデル・状態を自動で補正ルール候補にする。
3. ユーザーが画面から補正ルールを追加・無効化できるUIを追加する。
