# Boot the Hermes Agent (messaging gateway + cron scheduler). Windows PowerShell.
# Model creds come from docker/agent.env, which is copied to .hermes-data/.env —
# the file Hermes reads at /opt/data/.env (the provider auto-detects from the key).
#
#   1. Copy-Item docker/agent.env.example docker/agent.env   # set ONE provider + paste key
#   2. ./docker/run-gateway.ps1
#
# `gateway` is the messaging/cron service; use `hermes chat` for an interactive
# turn, `hermes proxy` for a local OpenAI-compatible API.

$ErrorActionPreference = "Stop"
$Root    = Split-Path -Parent $PSScriptRoot
$EnvSrc  = Join-Path $PSScriptRoot "agent.env"
$Data    = Join-Path $Root ".hermes-data"
$Skills  = Join-Path $Root "skills"
New-Item -ItemType Directory -Force -Path $Data | Out-Null

if (-not (Test-Path $EnvSrc)) {
  Write-Error "Missing docker/agent.env — Copy-Item docker/agent.env.example docker/agent.env (then set provider + key)"
}
Copy-Item $EnvSrc (Join-Path $Data ".env") -Force   # Hermes reads /opt/data/.env

docker run --rm -it `
  --name stackfund-hermes-gateway `
  -p 8642:8642 `
  -v "${Data}:/opt/data" `
  -v "${Skills}:/opt/data/skills/research:ro" `
  nousresearch/hermes-agent:latest gateway run
