# Run the StackFund agent (Hermes harness + deterministic engine + skills) on a
# one-shot prompt. The agent autonomously runs the StackFund pipeline via its
# skills and interprets the real numbers. This is the demo command. (Windows.)
#
# Prereqs:
#   1. docker build -f docker/Dockerfile.agent -t stackfund-agent:dev .
#   2. docker/agent.env set (OPENAI_API_KEY + OPENAI_BASE_URL for your gateway)
#   3. one-time: ./docker/setup-custom-model.sh   (registers the custom provider+key)
#
# Usage:
#   ./docker/run-agent.ps1
#   ./docker/run-agent.ps1 "Research 0056 with the etf-analysis skill"
param([string]$Prompt = "")

$ErrorActionPreference = "Stop"
$Root    = Split-Path -Parent $PSScriptRoot
$EnvSrc  = Join-Path $PSScriptRoot "agent.env"
$Data    = Join-Path $Root ".hermes-data"
$Skills  = Join-Path $Root "skills"
$Image    = if ($env:STACKFUND_AGENT_IMAGE) { $env:STACKFUND_AGENT_IMAGE } else { "stackfund-agent:dev" }
$Model    = if ($env:HERMES_MODEL)    { $env:HERMES_MODEL }    else { "gpt-5.5" }
$Provider = if ($env:HERMES_PROVIDER) { $env:HERMES_PROVIDER } else { "custom" }
if (-not $Prompt) {
  $Prompt = "Use your stackfund-etf-analysis skill to run the StackFund research pipeline (execute the skill script to get real numbers), then summarize for each ETF (0050/0056/00878) the rebalance decision (REBALANCE/NO_ACTION) and the reason. Add one line that the crowd-scenario divergence is non-authoritative and not part of the decision."
}

if (-not (Test-Path $EnvSrc)) {
  Write-Error "Missing docker/agent.env — Copy-Item docker/agent.env.example docker/agent.env (then set gateway key)"
}
New-Item -ItemType Directory -Force -Path $Data | Out-Null
Copy-Item $EnvSrc (Join-Path $Data ".env") -Force

docker run --rm `
  --env-file $EnvSrc `
  -v "${Data}:/opt/data" `
  -v "${Skills}:/opt/data/skills/research:ro" `
  $Image `
  -z $Prompt -m $Model --provider $Provider
