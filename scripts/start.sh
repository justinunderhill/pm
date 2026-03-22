#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="pm-mvp:local"
CONTAINER_NAME="pm-mvp"
ENV_FILE="$ROOT_DIR/.env"

docker build -t "$IMAGE_NAME" "$ROOT_DIR"

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

RUN_ARGS=(--name "$CONTAINER_NAME" -p 8000:8000)
if [[ -f "$ENV_FILE" ]]; then
  RUN_ARGS+=(--env-file "$ENV_FILE")
fi

docker run -d "${RUN_ARGS[@]}" "$IMAGE_NAME" >/dev/null

echo "Container '$CONTAINER_NAME' is running at http://127.0.0.1:8000"
