# One-shot check that the Hermes model endpoint actually answers (needs your key).
# Prints the model's reply, then exits — proves NOUS_API_KEY + model id are live.
#
#   1. Copy-Item docker/agent.env.example docker/agent.env   # paste your NOUS_API_KEY
#   2. ./docker/verify-model.ps1

$ErrorActionPreference = "Stop"
$Root    = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $PSScriptRoot "agent.env"
$Data    = Join-Path $Root ".hermes-data"
New-Item -ItemType Directory -Force -Path $Data | Out-Null

if (-not (Test-Path $EnvFile)) {
  Write-Error "Missing docker/agent.env — Copy-Item docker/agent.env.example docker/agent.env (then paste NOUS_API_KEY)"
}

$model = "Hermes-4-70B"
foreach ($line in Get-Content $EnvFile) {
  if ($line -match '^\s*HERMES_MODEL\s*=\s*(.+?)\s*$') { $model = $Matches[1] }
}

docker run --rm `
  --env-file $EnvFile `
  -v "${Data}:/opt/data" `
  nousresearch/hermes-agent:latest `
  --provider nous-api -m $model -z "Reply with exactly: HERMES OK"
