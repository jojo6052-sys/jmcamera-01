#!/usr/bin/env sh
set -eu

run_runtime_smoke=false
if [ "${1:-}" = "--runtime-smoke" ]; then
  run_runtime_smoke=true
elif [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Usage: scripts/check_docker_access.sh [--runtime-smoke]

Checks Docker CLI, Docker daemon connectivity, and Docker Compose availability.
Use --runtime-smoke to also run a small container and verify this environment
has enough privileges to create/extract/start containers.
EOF
  exit 0
elif [ "${1:-}" != "" ]; then
  echo "Unknown option: $1" >&2
  echo "Usage: scripts/check_docker_access.sh [--runtime-smoke]" >&2
  exit 2
fi

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

if [ "$run_runtime_smoke" = true ]; then
  echo "Running Docker runtime smoke check with hello-world..."
  docker run --rm hello-world >/dev/null
  echo "Docker runtime smoke check passed."
fi
