# StackFund — Autonomous Taiwan ETF Research Desk

A self-operating **Hermes agent** that runs a micro-business: it does real ETF
research, **earns** (Stripe subscriptions), **spends** (Stripe-paid SaaS/compute,
with a hard cap and a *refused-spend* path), and pays its own way — proven by a
before/after **Operational P&L**. Built for the **Hermes Agent Accelerated
Business Hackathon** (NVIDIA × Stripe × Nous Research).

> **Research / education only. Not individualised investment advice. StackFund
> places no securities orders.** The crowd-scenario layer is *scenario rehearsal,
> not prediction*; synthetic personas, not real opinion; not backtested.

## Architecture — Core-B (ENGINE + FACE, firewalled)

> Full write-up: **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)** · 中文版 **[doc/ARCHITECTURE.zh-TW.md](doc/ARCHITECTURE.zh-TW.md)**

- **ENGINE** (deterministic Python trunk): `L1` data book (eligibility gate) →
  `L2` scorecard → `L4` portfolio manager → `L5` finops → `L6` audit. Computes
  every number. `L4` consumes a full **`AuthoritativeState`** (ScoreCard +
  PortfolioState + PolicySet + CostModel + MarketState) — never just a score —
  so `NO_ACTION` is first-class with machine-readable `reason_codes`, including
  *"rebalance not worth the transaction cost"* (`EXPECTED_BENEFIT_BELOW_TRANSACTION_COST`).
- **FACE** (non-authoritative narrative side-rail): `L3` crowd scenario engine.
  Reads only a *frozen, bucketed* `ScenarioSeed`; emits only a `CrowdNarrative`
  (a **categorical** crowd stance — *no numeric scalar* anything could wire back).
  The crowd-vs-engine **`NarrativeDivergence`** (`LOW/MEDIUM/HIGH` bucket,
  `non_authoritative`) is computed at *report* time by the Report Composer, which
  reads the L6 snapshot + the narrative but **never writes back** to a decision.

Ledgers are kept strictly separate — **Portfolio (simulated, no orders)** vs
**FinOps (Stripe, the business)** vs **Experiment** — so a Stripe test charge is
never shown as ETF investment P&L.

The firewall is **structural and machine-checked** — L4/L5 do not import L3, any
FACE artifact, or the report module (see `pyproject.toml` `import-linter`
contracts + `tests/test_firewall_no_imports.py` + `tests/test_l4_signature.py`).

### Docker ⊂ OpenShell ⊂ NemoClaw (layered, not alternatives)
```
StackFund agent (Hermes harness + skills + engine)
   ↓ packaged as        docker/Dockerfile.agent
Docker / OCI image
   ↓ launched by         policy/openshell.yaml   (Landlock + seccomp + netns + L7 proxy)
OpenShell sandbox
   ↓ orchestrated by     policy/nemoclaw-blueprint.yaml
NemoClaw (onboard, blueprint, inference routing)
```
Dockerizing is the foundation; OpenShell/NemoClaw wrap the container. See
[`policy/README.md`](policy/README.md).

## Repo layout
```
src/stackfund/        ENGINE: l1_databook l2_scorecard l4_portfolio l5_finops l6_audit
                      + l3_crowd (side-rail) + report/ (composer) + ledgers.py
                      + contracts/ (typed firewall) + cli.py
skills/               Agent Skills (SKILL.md + references/ + thin scripts/)
                        etf-analysis/   crowd-scenario/
schemas/              versioned JSON Schemas (ScenarioSeed, ContrarianSignal, …)
fixtures/             frozen ETF samples + baked replay scenario
tests/                firewall guards + schema validation + engine + CLI
docker/               Dockerfile.core, Dockerfile.agent, compose.yml, egress-proxy/
policy/               openshell.yaml, nemoclaw-blueprint.yaml
.github/workflows/    ci.yml  (ruff → import-linter → pytest → docker build)
doc/                  ARCHITECTURE.md (+ .zh-TW), StackFund_可行性報告.md, …_Mermaid.md
```

## Quickstart

### Local (uv)
```bash
uv sync                       # installs deps + dev tools
uv run python -m stackfund pipeline      # L1→L2→L4 (+earn/spend/refused + P&L)
uv run python -m stackfund crowd --symbol 0056   # L3 side-rail (dry-run)
uv run python -m stackfund verify        # determinism check
uv run pytest -q              # tests (incl. firewall)
uv run lint-imports           # architectural firewall contracts
```

### Docker
```bash
# Deterministic core (zero egress):
docker build -f docker/Dockerfile.core -t stackfund-core:dev .
docker run --rm --network none stackfund-core:dev pipeline

# Full two-service topology (core + Hermes agent + allowlisting egress proxy):
cp secrets/stripe_secret_key.txt.example secrets/stripe_secret_key.txt   # then edit
docker compose -f docker/compose.yml up --build
```
The `agent` image builds `FROM nousresearch/hermes-agent` and bakes the skills at
`/opt/data/skills/...`; mount host `~/.hermes` at `/opt/data` for persistent state.
Requires Docker Engine ≥ 28.

### Run the Hermes agent
Set **exactly one** provider block in `docker/agent.env` (copy from `.example`) —
the provider auto-detects from the key:
- **Nous (Hermes)** — `NOUS_API_KEY` (the simplest Hermes path).
- **Anthropic (Claude)** — `ANTHROPIC_API_KEY`.
- **OpenAI-compatible** — `OPENAI_API_KEY` + `OPENAI_BASE_URL` (OpenAI / OpenRouter /
  vLLM / Ollama / self-hosted Hermes-4).

```bash
cp docker/agent.env.example docker/agent.env     # set ONE block + paste key (git-ignored)
./docker/verify-model.sh                          # one-shot: prints the model's reply
./docker/run-gateway.sh                           # boot the agent (messaging + cron)
```
Windows: `docker/*.ps1`. The scripts copy `docker/agent.env` → `.hermes-data/.env`,
the file Hermes reads at `/opt/data/.env` (verified: docker `--env-file` is scrubbed
by the image's s6 init, so the data-dir `.env` is the reliable path). Keys are never
baked into an image. `gateway` is the messaging/cron service (boots under s6;
verified); use `hermes chat` for an interactive turn or `hermes proxy` for a local
OpenAI-compatible API. Image: `nousresearch/hermes-agent` (Docker Hub, ~5.3 GB).
**Hackathon note:** the submission must use a Hermes model — Nous, or an
OpenAI-compatible endpoint serving Hermes-4.

## Security model
- **Secrets are runtime-only** — never in an image layer (`ARG`/`ENV`/`COPY .env`
  are banned). Injected via compose secrets → `/run/secrets/*` or the OpenShell
  egress proxy. Use a Stripe **restricted TEST key** (`rk_test_…`).
- **Default-deny egress** — the core runs `--network none`; the agent reaches only
  an allowlist (Stripe + your LLM host) through a forward proxy.

## CI
`ruff` (lint+format) → `import-linter` (firewall) → `pytest` (firewall + schema)
→ `docker build` core + zero-network smoke test. (Optional Trivy scan — pin by
commit SHA; see `.github/workflows/ci.yml`.)

## Status / decisions
This is the dockerization + engine scaffold. Confirmed and baked in:
- **Model: a Nous Hermes model is REQUIRED** → use provider `nous-api` + your
  `NOUS_API_KEY` (paste into `docker/agent.env`); confirm the exact Hermes id with
  `hermes model`. Defaults also set in `policy/openshell.yaml` /
  `nemoclaw-blueprint.yaml`. **Verified:** the official image
  `nousresearch/hermes-agent` (**Docker Hub**, ~5.3 GB) boots the gateway under s6.
- **Stripe: use a sandbox** (`stripe sandbox create`) for isolated TEST keys
  (`rk_test_…`), injected at runtime via compose secrets — never baked into the image.

Still to verify before locking the demo:
1. **Stripe spend path on Windows** — Hermes' Stripe Link CLI is Linux/macOS +
   US-account only → run under WSL2, or do spend via the Stripe agent-toolkit/Issuing.
2. **Deliverable** — the required artifact is a **1–3 min demo video**
   (tweet @NousResearch + Discord). Confirm the deadline on the official channel.

## Licence
MIT. The crowd-scenario engine is a clean-room distillation (idea only) — see
[`skills/crowd-scenario/references/clean-room.md`](skills/crowd-scenario/references/clean-room.md).
