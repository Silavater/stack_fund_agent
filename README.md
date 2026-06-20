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

- **ENGINE** (deterministic Python trunk): `L1` data book → `L2` scorecard →
  `L4` portfolio manager → `L5` finops → `L6` audit. Computes every number.
  `NO_ACTION` is a first-class output.
- **FACE** (non-authoritative narrative side-rail): `L3` crowd scenario engine.
  Reads only a *frozen, bucketed* `ScenarioSeed`; emits only a `ContrarianSignal`
  (narrative + a bounded `contrarian_modifier ∈ [-1,+1]`, `is_authoritative=false`).
  **It never decides a number, never influences an action, and never writes back
  to the decision path.**

The firewall is **structural and machine-checked** — L4/L5 do not import L3 or
its signal (see `pyproject.toml` `import-linter` contracts +
`tests/test_firewall_no_imports.py` + `tests/test_l4_signature.py`).

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
                      + l3_crowd (side-rail) + contracts/ (typed firewall) + cli.py
skills/               Agent Skills (SKILL.md + references/ + thin scripts/)
                        etf-analysis/   crowd-scenario/
schemas/              versioned JSON Schemas (ScenarioSeed, ContrarianSignal, …)
fixtures/             frozen ETF samples + baked replay scenario
tests/                firewall guards + schema validation + engine + CLI
docker/               Dockerfile.core, Dockerfile.agent, compose.yml, egress-proxy/
policy/               openshell.yaml, nemoclaw-blueprint.yaml
.github/workflows/    ci.yml  (ruff → import-linter → pytest → docker build)
doc/                  StackFund_可行性報告.md, StackFund_架構分析_Mermaid.md
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

## Status / needs confirmation
This is the dockerization + engine scaffold. Before locking the demo, confirm:
1. **Stripe spend skill platform limits** — Hermes' Stripe Link CLI is
   Linux/macOS + US-account only (the dev box is Windows → run under WSL2, or do
   spend via the Stripe agent-toolkit/Issuing).
2. **Hermes image registry / ports** — `docker pull nousresearch/hermes-agent`
   (Docker Hub vs GHCR), confirm `8642`/`9119` + `/opt/data`.
3. **Hackathon deliverable** — the required artifact is a **1–3 min demo video**
   (tweet @NousResearch + Discord); repo/Docker are credibility, not compliance.
   Confirm the deadline on the official channel.

## Licence
MIT. The crowd-scenario engine is a clean-room distillation (idea only) — see
[`skills/crowd-scenario/references/clean-room.md`](skills/crowd-scenario/references/clean-room.md).
