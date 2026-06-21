#!/usr/bin/env bash
# One-time setup: register a custom OpenAI-compatible gateway as a Hermes "custom"
# provider, so the agent can use catalog-unknown models (e.g. gpt-5.5). Reads the
# key from docker/agent.env (OPENAI_API_KEY); writes the gitignored .hermes-data/
# config.yaml (custom_providers + model.*) and auth.json (credential pool).
# Idempotent — safe to re-run.
#
#   ./docker/setup-custom-model.sh
#   NAME=y2k BASE_URL=http://y2k-admin-server:8317/v1 MODEL=gpt-5.5 ./docker/setup-custom-model.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SRC="${ROOT}/docker/agent.env"
DATA="${ROOT}/.hermes-data"
PYHELP="${ROOT}/docker/setup_custom_provider.py"
IMAGE="${HERMES_IMAGE:-nousresearch/hermes-agent:latest}"
NAME="${NAME:-y2k}"
BASE_URL="${BASE_URL:-http://y2k-admin-server:8317/v1}"
MODEL="${MODEL:-gpt-5.5}"

if [ ! -f "${ENV_SRC}" ]; then
  echo "Missing ${ENV_SRC} — cp docker/agent.env.example docker/agent.env (then set OPENAI_API_KEY + OPENAI_BASE_URL)" >&2
  exit 1
fi
mkdir -p "${DATA}"
cp "${ENV_SRC}" "${DATA}/.env"

DOCK_DATA="${DATA}"; DOCK_ENV="${ENV_SRC}"; DOCK_PY="${PYHELP}"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    export MSYS_NO_PATHCONV=1
    if command -v cygpath >/dev/null 2>&1; then
      DOCK_DATA="$(cygpath -m "${DATA}")"
      DOCK_ENV="$(cygpath -m "${ENV_SRC}")"
      DOCK_PY="$(cygpath -m "${PYHELP}")"
    fi
    ;;
esac

# The key is passed from the container's env ($OPENAI_API_KEY via --env-file); it
# is never echoed. auth add boots Hermes once (seeding config.yaml), then the
# python helper injects the custom_providers entry + model block.
docker run --rm \
  --env-file "${DOCK_ENV}" \
  -v "${DOCK_DATA}:/opt/data" \
  -v "${DOCK_PY}:/opt/setup_custom_provider.py:ro" \
  --entrypoint sh "${IMAGE}" -c "
. /opt/hermes/.venv/bin/activate 2>/dev/null
export HOME=/opt/data HERMES_HOME=/opt/data
hermes auth add custom:${NAME} --type api-key --api-key \"\$OPENAI_API_KEY\" --label '${NAME}-gateway' 2>&1 | tail -1
python /opt/setup_custom_provider.py '${NAME}' '${BASE_URL}' '${MODEL}'
hermes auth list 2>&1 | grep -i 'custom:${NAME}' || true
"

echo "Done — registered custom:${NAME} -> ${MODEL}. Verify with: ./docker/verify-model.sh"
