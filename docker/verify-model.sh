#!/usr/bin/env bash
# One-shot check that the Hermes model endpoint actually answers (needs your key).
# Prints the model's reply, then exits — proves NOUS_API_KEY + model id are live.
#
#   1. cp docker/agent.env.example docker/agent.env   # paste your NOUS_API_KEY
#   2. ./docker/verify-model.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT}/docker/agent.env"
DATA="${ROOT}/.hermes-data"
mkdir -p "${DATA}"

if [ ! -f "${ENV_FILE}" ]; then
  echo "Missing ${ENV_FILE} — run: cp docker/agent.env.example docker/agent.env  (then paste NOUS_API_KEY)" >&2
  exit 1
fi
set -a; . "${ENV_FILE}"; set +a
MODEL="${HERMES_MODEL:-Hermes-4-70B}"

exec docker run --rm \
  --env-file "${ENV_FILE}" \
  -e HERMES_UID="$(id -u)" -e HERMES_GID="$(id -g)" \
  -v "${DATA}:/opt/data" \
  nousresearch/hermes-agent:latest \
  --provider nous-api -m "${MODEL}" -z "Reply with exactly: HERMES OK"
