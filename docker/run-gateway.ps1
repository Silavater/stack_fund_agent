# Boot the Hermes Agent (messaging gateway + cron scheduler) with the REQUIRED
# Hermes model via the Nous Portal API key. Windows PowerShell.
#
#   1. Copy-Item docker/agent.env.example docker/agent.env   # paste your NOUS_API_KEY
#   2. ./docker/run-gateway.ps1
#
# The Hermes key is injected at RUNTIME (--env-file), never baked into an image.
# Note: `gateway` is the messaging/cron service. For an interactive turn use
# `hermes chat`; for a local OpenAI-compatible API use `hermes proxy`.

$ErrorActionPreference = "Stop"
$Root    = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $PSScriptRoot "agent.env"
$Data    = Join-Path $Root ".hermes-data"
$Skills  = Join-Path $Root "skills"
New-Item -ItemType Directory -Force -Path $Data | Out-Null

if (-not (Test-Path $EnvFile)) {
  Write-Error "Missing docker/agent.env — Copy-Item docker/agent.env.example docker/agent.env (then paste NOUS_API_KEY)"
}

# Read HERMES_MODEL from the env file for the -m flag (key itself goes via --env-file)
$model = "Hermes-4-70B"
foreach ($line in Get-Content $EnvFile) {
  if ($line -match '^\s*HERMES_MODEL\s*=\s*(.+?)\s*$') { $model = $Matches[1] }
}

docker run --rm -it `
  --name stackfund-hermes-gateway `
  --env-file $EnvFile `
  -p 8642:8642 `
  -v "${Data}:/opt/data" `
  -v "${Skills}:/opt/data/skills/research:ro" `
  nousresearch/hermes-agent:latest `
  --provider nous-api -m $model gateway run
