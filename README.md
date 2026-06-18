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


## GitHub remote / Phaseブランチ運用
このリポジトリのGitHub remoteは以下です。

```bash
git remote add origin https://github.com/jojo6052-sys/jmcamera-01.git
git fetch origin --prune
```

Phase単位で作業する場合は、mainを最新化してからfeatureブランチを作成・更新します。

```bash
git checkout -b feature/mvp-phase-1 origin/main
# 既にwork等で作業している場合は、必要に応じてブランチ名を変更してmainを取り込みます
git branch -m feature/mvp-phase-1
git fetch origin --prune
git rebase origin/main
```

同じPhaseの作業中は新しいPRを作らず、同じ `feature/mvp-phase-1` ブランチへ追加コミットします。pushにはGitHub認証が必要です。

```bash
git push -u origin feature/mvp-phase-1
```

> PATやAPIキーはチャット・コード・ログに貼らず、GitHub CLI/credential helper/SSH keyなど安全な認証手段を使ってください。

## セットアップ
```bash
cp .env.example .env
docker compose up --build
```

FrontendはVite 8系のため Node.js 20.19以上（または22.12以上）が必要です。Docker環境では `frontend/Dockerfile` の `node:20.19-alpine` を使います。

`docker-compose.yml` には db / redis / backend / frontend の healthcheck を設定しているため、起動後は以下で状態を確認できます。

```bash
docker compose ps
```

## 動作確認
- Backend health: `http://localhost:8001/health`
- API health: `http://localhost:8001/api/health`
- Phase status API: `http://localhost:8001/api/phase/status`
- Frontend: `http://localhost:5173`（初期表示は `Phase Status` タブ）
- Compose services: `docker compose ps` で `healthy` / `running` を確認

## Alembic / DBマイグレーション
backendコンテナは起動時に `RUN_MIGRATIONS=true`（デフォルト）で `alembic upgrade head` を実行します。手動で再実行する場合は以下です。

```bash
docker compose exec backend alembic upgrade head
```

自動マイグレーションを止めたい場合は `.env` の `RUN_MIGRATIONS=false` を設定してください。

## システムマニュアル
このシステムの目的、全体構成、大まかな使い方、Phase 1 MVPの見方、将来ロードマップは [`docs/system-manual.md`](docs/system-manual.md) にまとめています。Frontendにも `System Manual` タブを追加しているため、ブラウザ上で同じ流れを確認できます。

## 進捗ロードマップ
未完成部分と進捗の見える化は [`docs/progress.md`](docs/progress.md) にまとめています。Frontendの `Progress` タブでも、ローカルMVP、本番設定、外部データ取得、推薦ロジック、CI/運用の進捗と残タスクを確認できます。

## Phase 1 MVPに含まれる主要機能
- CSVインポートとProduct Analytics
- Search Keywords管理とYahoo候補取得
- Recommendationsでの候補確認、推薦スコア再計算、フィードバック保存、CSV出力
- Competitor ResearchでのeBayセラー分析、Sold HTML代替インポート、推奨検索KW保存
- eBay Marketplace Account Deletion endpoint
- Phase Status API / 画面によるDB接続・主要データ件数・設定状態確認


## Dev Check（Phase PR前の一括確認）
Phase単位PRを作成する前に、backendテスト・Alembic適用確認・frontend build・差分チェックをまとめて実行できます。Python依存関係は 3.11〜3.13 を優先して仮想環境にインストールします。

```bash
scripts/dev_check.sh
```

Docker Compose設定も含めて確認したい場合は、Docker CLIが使える環境で以下を実行してください。

```bash
RUN_DOCKER_CHECKS=true scripts/dev_check.sh
```

`RUN_DOCKER_CHECKS=true` は `docker compose config` まで確認します。実際の起動確認は `docker compose up --build` と `python scripts/smoke_check.py --base-url http://localhost:8001 --include-write-checks` を併用してください。

## Docker CLIをエージェント環境から使えるようにする
Docker DesktopやComposeサービスがホスト側で起動していても、このエージェントが動くシェル/コンテナ内に `docker` CLI と Docker daemon への接続が無い場合、エージェントからは `docker: command not found` になります。まず以下で、この実行環境からDockerに到達できるか確認してください。

```bash
scripts/check_docker_access.sh
```

CLI/daemon疎通だけでなく、実際にコンテナをpull/extract/startできる権限まで確認する場合は以下を実行します。

```bash
scripts/check_docker_access.sh --runtime-smoke
```

失敗する場合は、エージェントが使う同じ環境に対して以下を設定します。

1. `docker version` と `docker compose version` が通るように Docker CLI / Compose plugin をインストールする。
2. Dockerが別ホストやDocker Desktop側で動いている場合は、エージェント環境へ Docker daemon を公開する。Linux/devcontainerでは `/var/run/docker.sock:/var/run/docker.sock` をマウントし、リモートdaemonでは `DOCKER_HOST` を設定する。
3. Docker Desktop + WSL を使う場合は、Docker DesktopのWSL integrationで、エージェントが実行されるdistroを有効化する。
4. 再度 `scripts/check_docker_access.sh --runtime-smoke` を実行し、成功したら `docker compose exec backend pytest -q` と `docker compose exec frontend npm run build` をエージェントから実行できる状態です。

詳細な設定例は [`docs/agent-docker-setup.md`](docs/agent-docker-setup.md) を参照してください。

## Smoke Check（起動後の主要API確認）
`docker compose up --build` 後、別ターミナルで主要な読み取りAPIをまとめて確認できます。

```bash
python scripts/smoke_check.py --base-url http://localhost:8001
```

このスクリプトは `/health`、`/api/health`、`/api/phase/status`、検索KW、候補、ライバルセラー、分析APIをread-onlyで確認します。

検索KW作成 → Yahoo候補取得 → 候補スコアリングまで確認したい場合は、ローカル検証DBにデータを作成するwrite smoke checkも実行できます。

```bash
python scripts/smoke_check.py --base-url http://localhost:8001 --include-write-checks
```

## Phase 1 Verify（次回動作確認用）
Backendのread-only smoke check、FrontendのReact app shell確認、write smoke flowをまとめて確認する場合は、Compose起動後に以下を実行します。

```bash
python scripts/phase1_verify.py --backend-base-url http://localhost:8001 --frontend-url http://localhost:5173
```

CIログや共有用にJSONで結果を残したい場合は `--json` を付けます。DBに検証データを作りたくない場合は `--skip-write-checks` を付けてください。

```bash
python scripts/phase1_verify.py --backend-base-url http://localhost:8001 --frontend-url http://localhost:5173 --json
python scripts/phase1_verify.py --backend-base-url http://localhost:8001 --frontend-url http://localhost:5173 --skip-write-checks
python scripts/phase1_verify.py --backend-base-url http://localhost:8001 --frontend-url http://localhost:5173 --report-file reports/phase1-verification.md
```


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
- `POST /api/yahoo/search`（デフォルトは安全なfallback候補生成で保存。`.env` の `YAHOO_FETCH_MODE=live` でYahoo検索ページ取得を明示的に有効化）
- `GET /api/candidates`
- `GET /api/candidates/{id}`

### Yahoo候補取得モード
MVPの安定検証では、外部サイトへアクセスしない `YAHOO_FETCH_MODE=fallback` をデフォルトにしています。実Yahoo検索ページ取得を検証する場合のみ以下を `.env` に設定してください。

```env
YAHOO_FETCH_MODE=live
YAHOO_REQUEST_MIN_DELAY_SECONDS=0.2
YAHOO_REQUEST_MAX_DELAY_SECONDS=0.8
YAHOO_REQUEST_TIMEOUT_SECONDS=10
```

`live` モードでも取得失敗・ページ構造変更・アクセス制限時はfallback候補を返し、API全体を落とさない設計です。過剰アクセスを避けるため、ランダム待機とtimeoutを設定値で制御します。

## 推薦スコア学習・補正
推薦スコアは販売写真、説明欄、販売者評価、手動補正ルールを考慮します。ユーザー知見をあとから追加する `scoring_rules` APIの使い方は [`docs/scoring-learning.md`](docs/scoring-learning.md) を参照してください。

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
- Phase status: http://localhost:8001/api/phase/status
- Compose状態: `docker compose ps` で db / redis / backend / frontend のhealthを確認

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
- `GET /api/competitors/{seller_id}/insights`: Sold比率、平均価格差、Sold頻出語、推奨検索KWなどの簡易リサーチ指標を取得
- `POST /api/competitors/{seller_id}/keywords`: Sold頻出語やリサーチ語句を `search_keywords` に保存（単体/一括）
- `GET /api/competitors/{seller_id}/export.csv`: 現在のライバル商品フィルタをCSV出力
- Frontendは `Competitor Research` タブでセラーURL投入、出品中 / Sold Items の取り込み、保存済みセラー比較、商品一覧確認、簡易リサーチ指標、推奨検索KW/頻出語からの単体・一括キーワード保存、CSV出力に対応

### eBayセラーURL例
```text
https://www.ebay.com/str/example-seller
https://www.ebay.com/usr/example-seller
https://www.ebay.com/sch/i.html?_ssn=example-seller
```

> 注意: MVPではeBayの公開検索ページを控えめに取得して解析します。eBayが自動取得を403 Forbiddenで拒否した場合は `fetch_status=blocked`、その他のページ構造変更・アクセス制限時は `fetch_status=failed` としてセラー情報だけを残し、API全体は落とさない設計です。公開ページ取得を止めたい場合は `.env` の `EBAY_PUBLIC_FETCH_MODE=disabled` を設定し、Browse APIまたは保存HTMLインポートを使ってください。


## MVP Phase Status
Phase単位でPRをまとめる運用に合わせ、現在のMVPが起動・DB接続・主要API観点でどこまで確認できているかを一覧する導線を追加しています。

- `GET /api/phase/status`: DB接続確認、主要テーブル件数、Phase 1 ready check、eBay API / Marketplace Account Deletion設定状況を返す
- Frontend `Phase Status` タブ: 上記APIを表示し、Docker起動後の最初の確認画面として利用できる

```bash
curl -s http://localhost:8001/api/phase/status | python -m json.tool
```

`status=ready_with_configuration_pending` の場合でも、未設定の外部連携（例: eBay compliance endpoint URL / verification token）が残っていることを示すだけで、ローカルMVP機能そのものは確認できます。

### Phase 1 MVP 検証済み項目と次PR候補
- 検証済み: Docker Compose起動、`/health`、`/api/health`、`/api/phase/status`、read/write smoke check、backend pytest、frontend build。
- `core_ready=true`: CSVインポート、分析API/画面、検索KW、Yahoo候補、推薦スコア、フィードバック、ライバル分析のローカルMVP導線は確認済みとして扱う。
- `status=ready_with_configuration_pending`: ローカルMVPはreadyだが、Production向けの eBay API credentials / Marketplace Account Deletion endpoint 設定が未完了であることを示す。
- 外部設定: eBay Production keyset取得後に `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` を設定し、外部公開HTTPS URL確定後にMarketplace Account Deletion endpoint URL / verification tokenを設定する。
- Follow-up候補: Yahoo取得の本番差し替え・レート制御強化、eBay Sold履歴の公式API/許可済み導線、npm auditで検出されるfrontend依存脆弱性の精査を次PR候補にする。

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

## eBay公開ページ取得モード（MVP fallback）
Competitor Researchの公開検索ページ取得は、過剰アクセス防止のためdelay/timeoutを `.env` で制御できます。デフォルトは現状互換の `live` です。

```env
EBAY_PUBLIC_FETCH_MODE=live
EBAY_PUBLIC_REQUEST_MIN_DELAY_SECONDS=0.2
EBAY_PUBLIC_REQUEST_MAX_DELAY_SECONDS=0.8
EBAY_PUBLIC_REQUEST_TIMEOUT_SECONDS=12
```

公開ページ取得を行わず、eBay Browse API（出品中）や保存HTMLインポート（Sold Items）だけで検証する場合は `EBAY_PUBLIC_FETCH_MODE=disabled` を設定してください。

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
