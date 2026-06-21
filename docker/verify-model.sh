#!/usr/bin/env bash
# One-shot check that the configured model endpoint actually answers (needs your
# key). Copies docker/agent.env -> .hermes-data/.env, sends one prompt, prints the
# reply, exits. Works for any provider (nous-api / anthropic / openai-compatible).
#
#   1. cp docker/agent.env.example docker/agent.env   # set ONE provider + paste key
#   2. ./docker/verify-model.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SRC="${ROOT}/docker/agent.env"
DATA="${ROOT}/.hermes-data"
mkdir -p "${DATA}"

if [ ! -f "${ENV_SRC}" ]; then
  echo "Missing ${ENV_SRC} — run: cp docker/agent.env.example docker/agent.env  (then set provider + key)" >&2
  exit 1
fi
cp "${ENV_SRC}" "${DATA}/.env"

# See run-gateway.sh: only pass HERMES_UID when it's a real Linux uid.
UIDOPT=()
_huid="$(id -u 2>/dev/null || echo 0)"
if [ "${_huid}" -ge 1 ] && [ "${_huid}" -lt 65536 ]; then
  UIDOPT=(-e "HERMES_UID=${_huid}" -e "HERMES_GID=$(id -g)")
fi

# Model/provider passed explicitly so Hermes skips model-name auto-detection
# (which would override an OpenAI-compatible custom endpoint). Override via env.
MODEL="${HERMES_MODEL:-gpt-5.5}"
PROVIDER="${HERMES_PROVIDER:-custom}"

# Git Bash / MSYS (Windows) rewrites the container side of -v/--env-file paths and
# breaks the bind mount (symptom: agent runs against an empty data dir -> no final
# response). Disable conversion and hand docker a native C:/ path.
DOCK_DATA="${DATA}"; DOCK_ENV="${ENV_SRC}"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    export MSYS_NO_PATHCONV=1
    if command -v cygpath >/dev/null 2>&1; then
      DOCK_DATA="$(cygpath -m "${DATA}")"
      DOCK_ENV="$(cygpath -m "${ENV_SRC}")"
    fi
    ;;
esac

exec docker run --rm \
  --env-file "${DOCK_ENV}" \
  "${UIDOPT[@]}" \
  -v "${DOCK_DATA}:/opt/data" \
  nousresearch/hermes-agent:latest -z "Reply with exactly: HERMES OK" -m "${MODEL}" --provider "${PROVIDER}"
