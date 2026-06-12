#!/usr/bin/env bash
# Start FinAlly in Docker. Idempotent; pass --build to force a rebuild.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE=finally
CONTAINER=finally

if [[ "${1:-}" == "--build" ]] || ! docker image inspect "$IMAGE" > /dev/null 2>&1; then
    docker build -t "$IMAGE" .
fi

docker rm -f "$CONTAINER" > /dev/null 2>&1 || true

ENV_ARGS=()
[[ -f .env ]] && ENV_ARGS=(--env-file .env)

docker run -d --name "$CONTAINER" -p 8000:8000 -v finally-data:/app/db "${ENV_ARGS[@]+"${ENV_ARGS[@]}"}" "$IMAGE" > /dev/null

echo "FinAlly is running at http://localhost:8000"
command -v open > /dev/null && open http://localhost:8000 || true
