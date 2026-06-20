# One-shot check that the configured model endpoint actually answers (needs your
# key). Copies docker/agent.env -> .hermes-data/.env, sends one prompt, prints the
# reply, exits. Works for any provider (nous-api / anthropic / openai-compatible).
#
#   1. Copy-Item docker/agent.env.example docker/agent.env   # set ONE provider + paste key
#   2. ./docker/verify-model.ps1

$ErrorActionPreference = "Stop"
$Root   = Split-Path -Parent $PSScriptRoot
$EnvSrc = Join-Path $PSScriptRoot "agent.env"
$Data   = Join-Path $Root ".hermes-data"
New-Item -ItemType Directory -Force -Path $Data | Out-Null

if (-not (Test-Path $EnvSrc)) {
  Write-Error "Missing docker/agent.env — Copy-Item docker/agent.env.example docker/agent.env (then set provider + key)"
}
Copy-Item $EnvSrc (Join-Path $Data ".env") -Force

docker run --rm `
  -v "${Data}:/opt/data" `
  nousresearch/hermes-agent:latest -z "Reply with exactly: HERMES OK"
