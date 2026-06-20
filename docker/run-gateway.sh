#!/usr/bin/env bash
# Boot the Hermes Agent (messaging gateway + cron scheduler) with the REQUIRED
# Hermes model via the Nous Portal API key. bash / WSL2 / Linux / macOS.
#
#   1. cp docker/agent.env.example docker/agent.env   # paste your NOUS_API_KEY
#   2. ./docker/run-gateway.sh
#
# The Hermes key is injected at RUNTIME (--env-file), never baked into an image.
# Note: `gateway` is the messaging/cron service. For an interactive turn use
# `hermes chat`; for a local OpenAI-compatible API use `hermes proxy`.
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

exec docker run --rm -it \
  --name stackfund-hermes-gateway \
  --env-file "${ENV_FILE}" \
  -e HERMES_UID="$(id -u)" -e HERMES_GID="$(id -g)" \
  -p 8642:8642 \
  -v "${DATA}:/opt/data" \
  -v "${ROOT}/skills:/opt/data/skills/research:ro" \
  nousresearch/hermes-agent:latest \
  --provider nous-api -m "${MODEL}" gateway run
