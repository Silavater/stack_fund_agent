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

# Model/provider passed explicitly so Hermes skips model-name auto-detection
# (which would override an OpenAI-compatible custom endpoint). Override via env.
$Model    = if ($env:HERMES_MODEL)    { $env:HERMES_MODEL }    else { "gpt-5.5" }
$Provider = if ($env:HERMES_PROVIDER) { $env:HERMES_PROVIDER } else { "custom" }

docker run --rm `
  --env-file $EnvSrc `
  -v "${Data}:/opt/data" `
  nousresearch/hermes-agent:latest -z "Reply with exactly: HERMES OK" -m $Model --provider $Provider
