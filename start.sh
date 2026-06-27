#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_CANDIDATES=("$BACKEND_PORT" 8022 8021 8020 8023 8024 8001 8002 8010 8011)

backend_status() {
  local port="$1"
  local base="http://${BACKEND_HOST}:${port}"
  if curl -fsS "${base}/api/health" >/dev/null 2>&1 && curl -fsS "${base}/api/settings/ai" >/dev/null 2>&1; then
    echo compatible
    return
  fi
  if (echo >"/dev/tcp/${BACKEND_HOST}/${port}") >/dev/null 2>&1; then
    echo occupied
    return
  fi
  echo free
}

echo "Starting Storyworks Unified..."

selected_backend_port=""
selected_backend_mode=""
first_free_port=""
for port in "${BACKEND_CANDIDATES[@]}"; do
  status="$(backend_status "$port")"
  if [[ "$status" == "compatible" ]]; then
    selected_backend_port="$port"
    selected_backend_mode="existing"
    break
  fi
  if [[ "$status" == "free" && -z "$first_free_port" ]]; then
    first_free_port="$port"
  fi
done

if [[ -z "$selected_backend_port" ]]; then
  if [[ -n "$first_free_port" ]]; then
    selected_backend_port="$first_free_port"
    selected_backend_mode="start"
  else
    echo "ERROR: no compatible or free backend port was found." >&2
    exit 1
  fi
fi

BACKEND_URL="http://${BACKEND_HOST}:${selected_backend_port}"
export STORYWORKS_API_TARGET="$BACKEND_URL"

if [[ "$selected_backend_mode" == "existing" ]]; then
  echo "Backend ready: ${BACKEND_URL}"
else
  echo "Starting backend: ${BACKEND_URL}"
  (cd apps/backend && python run.py --host "$BACKEND_HOST" --port "$selected_backend_port") &
fi

if (echo >"/dev/tcp/127.0.0.1/${FRONTEND_PORT}") >/dev/null 2>&1; then
  echo "Frontend already running: http://localhost:${FRONTEND_PORT}"
  echo "Refresh the page if it was opened before this startup."
else
  (cd apps/frontend && npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT") &
fi

echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "Backend:  ${BACKEND_URL}"
wait
