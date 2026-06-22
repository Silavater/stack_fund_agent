#!/usr/bin/env bash
# StackFund's standing weekly research plan — the "long-term planning" beat.
#
# The schedulable unit is the deterministic engine journal (no LLM, no network):
#   python -m stackfund journal
# appends a dated decision entry to .hermes-data/research-journal.jsonl, shown at
# the web app's /journal page. Because it is deterministic, it is reliable to run
# unattended — the agent doesn't wait to be asked, it operates on a schedule.
#
# This script runs ONE entry now (proof) and prints the two ways to schedule it.
#
# ── A) Hermes cron — the agent owns the plan (needs the container + model gateway).
#    Runs an agent turn on a schedule. Verify flags against `hermes cron --help`
#    first (the schema varies by version), then:
#
#      docker exec stackfund-dashboard sh -lc '. /opt/hermes/.venv/bin/activate; \
#        export HOME=/opt/data HERMES_HOME=/opt/data; \
#        hermes cron add --name stackfund-weekly --schedule "0 9 * * 1" \
#          --prompt "Run your stackfund-etf-analysis skill for 0050/0056/00878, then run \
#                    python -m stackfund journal, and summarise the rebalance decisions."'
#      docker exec stackfund-dashboard sh -lc '... hermes cron list'
#
# ── B) Host scheduler on the engine (reliable, no gateway). Schedule the journal
#    command directly:
#      Linux / WSL2 (crontab -e):
#        0 9 * * 1  cd <repo> && uv run python -m stackfund journal
#      Windows Task Scheduler:
#        schtasks /Create /SC WEEKLY /D MON /TN StackFundWeekly /TR \
#          "cmd /c cd /d <repo> && uv run python -m stackfund journal"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "running one research-journal entry now ..."
( cd "${ROOT}" && uv run python -m stackfund journal )
echo
echo "scheduled? see this script's header — Hermes cron (A) or a host scheduler (B)."
echo "view the journal at the web app's /journal page  (bash docker/run-chat-ui.sh)"
