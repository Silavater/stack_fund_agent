# StackFund — Autonomous Taiwan ETF Research Desk

A self-operating **Hermes agent** that runs a micro-business: it does real ETF
research, **earns** (Stripe subscriptions), **spends** (Stripe-paid SaaS/compute,
with a hard cap and a *refused-spend* path), and pays its own way — proven by a
before/after **Operational P&L**. Built for the **Hermes Agent Accelerated
Business Hackathon** (NVIDIA × Stripe × Nous Research).

> **Research / education only. Not individualised investment advice. StackFund
> places no securities orders.** The crowd-scenario layer is *scenario rehearsal,
> not prediction*; synthetic personas, not real opinion; not backtested.

## 📖 Docs — where to start

| Read this | What it is |
|---|---|
| **[doc/DEMO.md](doc/DEMO.md)** | The demo walkthrough — the buy → research → ops journey |
| **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)** | The Core-B design: ENGINE + FACE, the firewall, L1–L6 |
| **[Feasibility report](doc/StackFund_Feasibility_Report.md)** · **[Architecture diagrams](doc/StackFund_Architecture_Mermaid.md)** | Deep dive: the full viability argument + 10 Mermaid diagrams |
| **[NOTICE](NOTICE)** · **[LICENSE](LICENSE)** | Third-party attribution + MIT licence |

> The agent itself is `agent/SOUL.md` (the persona) + `skills/` (the ETF-analysis & crowd-scenario Agent Skills); the sandbox policy is in `policy/`.

## Architecture — Core-B (ENGINE + FACE, firewalled)

> Full write-up: **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)**

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
schemas/              versioned JSON Schemas (ScenarioSeed, CrowdNarrative, …)
fixtures/             frozen ETF samples + baked replay scenario
tests/                firewall guards + schema validation + engine + CLI
docker/               Dockerfile.core, Dockerfile.agent, compose.yml, egress-proxy/
policy/               openshell.yaml, nemoclaw-blueprint.yaml
.github/workflows/    ci.yml  (ruff → import-linter → pytest → docker build)
doc/                  ARCHITECTURE.md, DEMO.md, StackFund_Feasibility_Report.md, StackFund_Architecture_Mermaid.md
```

## Quickstart

### Local (uv)
```bash
uv sync                       # installs deps + dev tools
uv run python -m stackfund fetch --symbol 0050 --live   # official TWSE price/volume (omit --live for frozen)
uv run python -m stackfund pipeline      # L1→L2→L4 (+earn/spend/refused + P&L)
uv run python -m stackfund pipeline --json   # same, as a structured JSON result
uv run python -m stackfund desk          # render a static HTML research desk → dist/stackfund-desk.html
uv run python -m stackfund crowd --symbol 0056   # L3 side-rail (dry-run)
uv run python -m stackfund verify        # determinism check
uv run python -m stackfund journal       # append a dated entry to the standing research journal
uv run python -m stackfund finops        # earn/spend/refused (stub) — add --live for real Stripe
# real Stripe (test mode):  uv sync --extra stripe; put rk_test_… in secrets/stripe_secret_key.txt
uv run python -m stackfund finops --live
uv run pytest -q              # tests (incl. firewall)
uv run lint-imports           # architectural firewall contracts
```

**Web app** (buy → use → ops · bilingual EN/中 · USD test-mode): `bash docker/run-chat-ui.sh`
(Windows: double-click `start-ui.cmd`) → open `http://localhost:5757/pricing`. Routes:
`/desk` (the **Board** — 8 ETFs + candlestick K-lines), `/finops`, `/journal` are public;
`/` (chat) is **Pro-gated** (`/signout` resets).
See [`doc/DEMO.md`](doc/DEMO.md).

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

## Demo mode — what's real vs. illustrative (read before judging)
- **Earn = real Stripe (TEST mode).** Subscribing on `/pricing` runs a real Stripe TEST
  Checkout (`cs_…/pi_…`, card `4242 4242 4242 4242`). This is the live money path.
- **Spend = the FinOps *logic* is real; autonomous execution is deferred.** The
  earn / spend / refused-spend ledger and the monthly-cap **refusal** (`$999 > headroom 380`)
  are computed and unit-tested. The agent *placing* a real Stripe spend is gated to Linux/US
  (Hermes' Stripe Link CLI), so it is not run on this Windows dev box — by design, not a gap.
- **Market data:** with `--live`, **price + volume are live** (TWSE + Yahoo); **ETF
  fundamentals are reference / fixture data** (the SITCA NAV scraper is a documented seam,
  not a shipped scraper). The default demo is **frozen** (real-but-fixed prices) and fully
  deterministic; `--live` is opt-in.
- **Securities orders: none, ever.** Every `RebalancePlan` is an illustrative research
  allocation — there is no order path.

**Deliverable:** a 1–3 min demo video (post to @NousResearch + the Nous Discord).

## Licence
MIT. The crowd-scenario engine is a clean-room distillation (idea only) — see
[`skills/crowd-scenario/references/clean-room.md`](skills/crowd-scenario/references/clean-room.md).
