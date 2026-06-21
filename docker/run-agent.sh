#!/usr/bin/env bash
# Run the StackFund agent (Hermes harness + deterministic engine + skills) on a
# one-shot prompt. The agent autonomously runs the StackFund pipeline via its
# skills and interprets the real numbers. This is the demo command.
#
# Prereqs:
#   1. docker build -f docker/Dockerfile.agent -t stackfund-agent:dev .
#   2. docker/agent.env set (OPENAI_API_KEY + OPENAI_BASE_URL for your gateway)
#   3. one-time: ./docker/setup-custom-model.sh   (registers the custom provider+key)
#
# Usage:
#   ./docker/run-agent.sh                                  # default ETF-research prompt
#   ./docker/run-agent.sh "Research 0056 with the etf-analysis skill"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SRC="${ROOT}/docker/agent.env"
DATA="${ROOT}/.hermes-data"
SKILLS="${ROOT}/skills"
IMAGE="${STACKFUND_AGENT_IMAGE:-stackfund-agent:dev}"
MODEL="${HERMES_MODEL:-gpt-5.5}"
PROVIDER="${HERMES_PROVIDER:-custom}"
PROMPT="${*:-Use your stackfund-etf-analysis skill to run the StackFund research pipeline (execute the skill script to get real numbers), then summarize for each ETF (0050/0056/00878) the rebalance decision (REBALANCE/NO_ACTION) and the reason. Add one line that the crowd-scenario divergence is non-authoritative and not part of the decision.}"

if [ ! -f "${ENV_SRC}" ]; then
  echo "Missing ${ENV_SRC} — cp docker/agent.env.example docker/agent.env (then set gateway key)" >&2
  exit 1
fi
mkdir -p "${DATA}"
cp "${ENV_SRC}" "${DATA}/.env"

# Git Bash / MSYS (Windows) rewrites the container side of -v/--env-file paths and
# breaks the bind mount. Disable conversion and hand docker native C:/ paths.
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

# --provider/-m explicit so Hermes skips model-name auto-detection (which would
# override an OpenAI-compatible custom endpoint). The engine is baked at
# /opt/stackfund; skills are mounted over the data-dir convention path.
exec docker run --rm \
  --env-file "${DOCK_ENV}" \
  -v "${DOCK_DATA}:/opt/data" \
  -v "${DOCK_SKILLS}:/opt/data/skills/research:ro" \
  "${IMAGE}" \
  -z "${PROMPT}" -m "${MODEL}" --provider "${PROVIDER}"
