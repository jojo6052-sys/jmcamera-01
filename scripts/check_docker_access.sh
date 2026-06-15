#!/usr/bin/env sh
set -eu

if ! command -v docker >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Docker CLI is not available in this execution environment.

To let this agent run Docker commands, expose Docker to the same shell/session used by the agent:
- Install Docker CLI in the agent environment, or use a devcontainer/image that includes it.
- If Docker is running on the host, mount the host Docker socket into the agent environment:
  /var/run/docker.sock:/var/run/docker.sock
- On Docker Desktop + WSL, enable integration for the distro/session where the agent runs.
- If using a remote Docker daemon, set DOCKER_HOST so `docker version` works from this shell.

After updating the environment, re-run:
  scripts/check_docker_access.sh
EOF
  exit 127
fi

docker version >/dev/null
docker compose version >/dev/null

echo "Docker CLI and Docker Compose are available."
docker compose ps
