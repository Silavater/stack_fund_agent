#!/usr/bin/env bash
# Boot the Hermes Agent (messaging gateway + cron scheduler).
# Model creds come from docker/agent.env, which is copied to .hermes-data/.env —
# the file Hermes reads at /opt/data/.env (the provider auto-detects from the key).
#
#   1. cp docker/agent.env.example docker/agent.env   # set ONE provider + paste key
#   2. ./docker/run-gateway.sh
#
# `gateway` is the messaging/cron service; use `hermes chat` for an interactive
# turn, `hermes proxy` for a local OpenAI-compatible API.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SRC="${ROOT}/docker/agent.env"
DATA="${ROOT}/.hermes-data"
mkdir -p "${DATA}"

if [ ! -f "${ENV_SRC}" ]; then
  echo "Missing ${ENV_SRC} — run: cp docker/agent.env.example docker/agent.env  (then set provider + key)" >&2
  exit 1
fi
cp "${ENV_SRC}" "${DATA}/.env"   # Hermes reads /opt/data/.env (process --env-file is scrubbed by s6)

# Own container-written files as you on Linux/WSL2; skip on Git-Bash-for-Windows
# whose MSYS uid is out of range and would block the bind-mounted .env read
# (Docker Desktop handles perms there anyway).
UIDOPT=()
_huid="$(id -u 2>/dev/null || echo 0)"
if [ "${_huid}" -ge 1 ] && [ "${_huid}" -lt 65536 ]; then
  UIDOPT=(-e "HERMES_UID=${_huid}" -e "HERMES_GID=$(id -g)")
fi

exec docker run --rm -it \
  --name stackfund-hermes-gateway \
  "${UIDOPT[@]}" \
  -p 8642:8642 \
  -v "${DATA}:/opt/data" \
  -v "${ROOT}/skills:/opt/data/skills/research:ro" \
  nousresearch/hermes-agent:latest gateway run
