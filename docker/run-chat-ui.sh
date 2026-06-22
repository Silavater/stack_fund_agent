#!/usr/bin/env bash
# StackFund conversational UI — a branded chat page backed by the Hermes agent.
# Ensures an agent container is running (engine + skills + SOUL), then serves a
# dependency-free chat server at http://localhost:5757. Each message runs one real
# agent turn (gpt-5.5 → skills → engine), ~15-25s.
#
#   ./docker/run-chat-ui.sh        # then open http://localhost:5757
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SRC="${ROOT}/docker/agent.env"
DATA="${ROOT}/.hermes-data"
SKILLS="${ROOT}/skills"
IMAGE="${STACKFUND_AGENT_IMAGE:-stackfund-agent:dev}"
CONTAINER="${SF_AGENT_CONTAINER:-stackfund-agent}"
PORT="${SF_UI_PORT:-5757}"

if [ ! -f "${ENV_SRC}" ]; then
  echo "Missing ${ENV_SRC} — cp docker/agent.env.example docker/agent.env (then set gateway key)" >&2
  exit 1
fi
mkdir -p "${DATA}"
cp "${ENV_SRC}" "${DATA}/.env"
if [ -f "${ROOT}/agent/SOUL.md" ]; then
  rm -f "${DATA}/SOUL.md" 2>/dev/null || true
  cp "${ROOT}/agent/SOUL.md" "${DATA}/SOUL.md"
fi

DOCK_DATA="${DATA}"; DOCK_ENV="${ENV_SRC}"; DOCK_SKILLS="${SKILLS}"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    export MSYS_NO_PATHCONV=1
    if command -v cygpath >/dev/null 2>&1; then
      DOCK_DATA="$(cygpath -m "${DATA}")"
      DOCK_ENV="$(cygpath -m "${ENV_SRC}")"
      DOCK_SKILLS="$(cygpath -m "${SKILLS}")"
    fi
    ;;
esac

if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER}"; then
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
  echo "starting agent container ${CONTAINER} ..."
  docker run -d --name "${CONTAINER}" \
    --env-file "${DOCK_ENV}" \
    -v "${DOCK_DATA}:/opt/data" \
    -v "${DOCK_SKILLS}:/opt/data/skills/research:ro" \
    "${IMAGE}" gateway run >/dev/null
  printf "waiting for agent init"
  for _ in $(seq 1 30); do
    if docker exec "${CONTAINER}" sh -lc \
        '. /opt/hermes/.venv/bin/activate 2>/dev/null; hermes --version >/dev/null 2>&1'; then
      echo " ready"
      break
    fi
    printf "."
    sleep 2
  done
fi

echo "agent container: ${CONTAINER}  ·  open http://localhost:${PORT}/pricing"
# `uv run --extra stripe` so the server can import stackfund + the Stripe SDK
# (real test-mode Checkout). Without uv/stripe it still runs, with a stub checkout.
SF_AGENT_CONTAINER="${CONTAINER}" SF_UI_PORT="${PORT}" \
  uv run --extra stripe python "${ROOT}/ui/server.py"
