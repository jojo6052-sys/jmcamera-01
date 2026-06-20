# Agent Docker setup guide

このエージェントから `docker compose ...` を実行するには、Docker Desktopがホスト側で起動しているだけでなく、エージェントが動く実行環境からDocker daemonへ接続できる必要があります。

## まず確認すること

エージェント環境で以下が成功すれば、CLI・daemon・実コンテナ起動権限まで揃っています。

```bash
scripts/check_docker_access.sh --runtime-smoke
```

`docker version` や `docker compose version` だけ成功しても、`--runtime-smoke` が `unshare: operation not permitted` や `operation not permitted` で失敗する場合は、コンテナ実行に必要な権限が不足しています。

## 推奨: ホストDocker Desktopのsocketをエージェントへ渡す

エージェントがdevcontainerやDockerコンテナ内で動いている場合は、内側でDocker daemonを起動するより、ホスト側Docker Desktopのdaemon socketを渡す構成が安定します。

### devcontainerの場合

`.devcontainer/devcontainer.json` など、エージェント実行コンテナの設定に以下を追加します。

```json
{
  "mounts": [
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
  ],
  "features": {
    "ghcr.io/devcontainers/features/docker-outside-of-docker:1": {}
  }
}
```

再作成後、エージェント環境で以下を確認します。

```bash
docker version
docker compose version
scripts/check_docker_access.sh --runtime-smoke
```

### Docker runでエージェント環境を起動している場合

起動オプションにDocker socketを追加します。

```bash
docker run \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD:/workspace/jmcamera-01" \
  -w /workspace/jmcamera-01 \
  <agent-image>
```

コンテナ内にDocker CLIが無い場合は、Docker CLI入りのイメージを使うか、`docker.io` / `docker-compose-v2` 相当をインストールしてください。

## Docker Desktop + WSLの場合

1. Docker Desktopを起動する。
2. Docker Desktopの `Settings > Resources > WSL integration` を開く。
3. エージェントが実行されるWSL distroを有効化する。
4. そのdistro内で以下を確認する。

```bash
docker version
docker compose version
scripts/check_docker_access.sh --runtime-smoke
```

## remote Docker daemonを使う場合

Docker daemonをTCP/TLSなどで公開している場合は、エージェント環境に `DOCKER_HOST` を設定します。

```bash
export DOCKER_HOST=tcp://<docker-host>:2376
# TLS利用時は環境に合わせて DOCKER_TLS_VERIFY / DOCKER_CERT_PATH も設定
scripts/check_docker_access.sh --runtime-smoke
```

## 最終確認コマンド

`--runtime-smoke` が通ったら、JM Cameraの標準確認を実行します。

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose exec backend pytest -q
docker compose exec backend python -m compileall app
docker compose exec frontend npm run build
python scripts/phase1_verify.py --backend-base-url http://localhost:8001 --frontend-url http://localhost:5173 --report-file reports/phase1-verification.md
```

## よくある失敗

- `docker: command not found`: エージェント環境にDocker CLIがありません。Docker CLI入り環境にするかCLIをインストールしてください。
- `Cannot connect to the Docker daemon`: Docker socketがマウントされていない、または `DOCKER_HOST` が未設定/誤設定です。
- `unshare: operation not permitted` / `mount: operation not permitted`: Docker daemonは見えていますが、実行環境の権限が不足しています。ホストDocker Desktopのsocketを渡すか、privileged相当の環境で起動してください。
- Composeの環境変数警告: `.env` が無い可能性があります。`cp .env.example .env` を実行してください。
