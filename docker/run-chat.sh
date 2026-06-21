#!/usr/bin/env bash
# Interactive chat with the StackFund agent (Hermes harness + engine + skills).
# Type a request (e.g. "research 0056 with the etf-analysis skill") and watch the
# agent run the skills live. Leave with /exit or Ctrl+C.
#
# Prereqs: build the image + run setup once (see docker/run-agent.sh header).
#   ./docker/run-chat.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SRC="${ROOT}/docker/agent.env"
DATA="${ROOT}/.hermes-data"
SKILLS="${ROOT}/skills"
IMAGE="${STACKFUND_AGENT_IMAGE:-stackfund-agent:dev}"
MODEL="${HERMES_MODEL:-gpt-5.5}"
PROVIDER="${HERMES_PROVIDER:-custom}"

if [ ! -f "${ENV_SRC}" ]; then
  echo "Missing ${ENV_SRC} — cp docker/agent.env.example docker/agent.env (then set gateway key)" >&2
  exit 1
fi
mkdir -p "${DATA}"
cp "${ENV_SRC}" "${DATA}/.env"

# Refresh the StackFund agent identity (always-loaded SOUL.md); clear the read-only stub.
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

exec docker run --rm -it \
  --env-file "${DOCK_ENV}" \
  -v "${DOCK_DATA}:/opt/data" \
  -v "${DOCK_SKILLS}:/opt/data/skills/research:ro" \
  "${IMAGE}" \
  chat -m "${MODEL}" --provider "${PROVIDER}"
