"""StackFund CLI — the composition root that wires ENGINE + FACE.

Subcommands:
  pipeline   run L1->L2->L4 over fixtures with full AuthoritativeState, render the
             L3 crowd FACE as a non-authoritative divergence, and print the three
             separate ledgers (Portfolio / FinOps / Experiment).
  crowd      run only the L3 crowd side-rail for one ETF (dry-run by default).
  verify     offline determinism check: same seed -> same crowd consensus.

Importing the crowd side-rail (L3) and the report composer here is fine — the CLI
is the composition root. The firewall forbids *L4/L5* from importing the crowd
side, not the CLI.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from stackfund.contracts.authoritative_state import AuthoritativeState
from stackfund.contracts.costs import CostModel
from stackfund.contracts.market import MarketState
from stackfund.contracts.policy import PolicySet
from stackfund.contracts.portfolio import PortfolioState
from stackfund.l1_databook import (
    SitcaFundamentals,
    load_databook,
    load_databook_from_fixture,
    make_seed,
)
from stackfund.l1_databook.book import LIVE_MOMENTUM_FIELDS, LIVE_PRICE_FIELDS
from stackfund.l2_scorecard import build_scorecard
from stackfund.l3_crowd import run_scenario
from stackfund.l4_portfolio import build_rebalance_plan
from stackfund.l5_finops import (
    EARN,
    SPEND,
    attempt_spend,
    make_receipt,
    operational_pnl,
    record_earn,
)
from stackfund.l6_audit import crowd_report_provenance, decision_provenance
from stackfund.ledgers import experiment_ledger, finops_ledger, portfolio_ledger
from stackfund.report import compose_divergence
from stackfund.report.desk import render_desk_html


def _fixtures_dir() -> Path:
    override = os.environ.get("STACKFUND_FIXTURES")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "fixtures"


def _load_portfolio() -> PortfolioState:
    path = _fixtures_dir() / "portfolio.json"
    if not path.exists():
        return PortfolioState(holdings={}, cash_weight=1.0)
    data = json.loads(path.read_text(encoding="utf-8"))
    return PortfolioState(
        holdings=data.get("holdings", {}),
        cash_weight=data.get("cash_weight", 1.0),
        as_of=data.get("as_of", ""),
    )


def build_pipeline_result(symbols: list[str], scenario: str, seed: int) -> dict:
    """Run L1->L2->L4 + L3 FACE + L5 ledgers; return a structured, JSON-able dict.

    Single compute path: ``cmd_pipeline`` renders it as text/JSON, ``cmd_desk``
    renders it as a static HTML research-desk view. L4 still consumes only an
    ``AuthoritativeState`` — the crowd FACE is read for divergence at report time.
    """
    portfolio = _load_portfolio()
    policy = PolicySet()
    costs = CostModel()
    market = MarketState(session="closed", as_of="2026-06-19")
    run_id = f"run_{seed}"

    receipts = [record_earn("earn_001", 299.0)]  # one Pro subscription (test-mode earn)
    cap_remaining = 500.0
    plans = []
    etfs: list[dict] = []

    for sym in symbols:
        book = load_databook_from_fixture(_fixtures_dir() / f"etf_{sym}.json")
        scorecard = build_scorecard(book)
        state = AuthoritativeState(scorecard, portfolio, policy, costs, market)
        plan = build_rebalance_plan(state)  # ENGINE: AuthoritativeState only, never FACE
        decision_provenance(plan)
        plans.append(plan)

        # FACE side-rail (dry-run): narrative only; divergence computed at report time.
        seed_obj = make_seed(book, market_scenario_label=scenario, rng_seed=seed)
        narrative = run_scenario(seed_obj, dry_run=True)
        divergence = compose_divergence(narrative, scorecard)
        crowd_report_provenance(narrative, divergence)

        row: dict = {
            "symbol": sym,
            "action": plan.action,
            "reason_codes": list(plan.reason_codes),
            "no_action_reason": plan.no_action_reason,
            "crowd_consensus": divergence.crowd_consensus,
            "engine_posture": divergence.engine_posture,
            "divergence_bucket": divergence.divergence_bucket,
        }
        if plan.deltas:
            d = plan.deltas[0]
            row.update(
                {
                    "delta_pp": round(d.hard_delta_pp, 2),
                    "target_weight_pct": round(d.target_weight_pct, 1),
                    "benefit_bps": d.benefit_bps,
                    "cost_bps": d.cost_bps,
                    "reasons": list(d.hard_reasons),
                }
            )
        etfs.append(row)

    # FinOps SPEND + REFUSED SPEND beat (the business, not ETFs)
    receipts.append(attempt_spend("spend_001", 120.0, cap_remaining))
    cap_remaining -= 120.0
    receipts.append(attempt_spend("spend_002", 999.0, cap_remaining))  # breaches cap -> refused
    pnl = operational_pnl("2026-06", receipts)

    fin = finops_ledger(run_id, receipts, pnl)
    port = portfolio_ledger(run_id, plans)
    exp = experiment_ledger(run_id, parent_run_id="none", rng_seed=seed, scenario_label=scenario)

    return {
        "meta": {
            "scenario": scenario,
            "seed": seed,
            "run_id": run_id,
            "formula_version": exp.formula_version,
            "as_of": market.as_of,
        },
        "etfs": etfs,
        "finops": {
            "revenue": fin.pnl.revenue,
            "cost": fin.pnl.cost,
            "gross_margin": fin.pnl.gross_margin,
            "refused": [{"reason": r.reason} for r in fin.receipts if r.type == "refused_spend"],
        },
        "portfolio": [
            {"symbol": e.etf_symbol, "action": e.action, "delta_pp": round(e.simulated_delta_pp, 2)}
            for e in port
        ],
        "experiment": {
            "run_id": exp.run_id,
            "seed": exp.rng_seed,
            "formula_version": exp.formula_version,
        },
    }


def cmd_pipeline(args: argparse.Namespace) -> int:
    symbols = args.symbols or ["0050", "0056", "00878"]
    result = build_pipeline_result(symbols, args.scenario, args.seed)
    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"=== StackFund pipeline (scenario={args.scenario!r}, seed={args.seed}) ===")
    for e in result["etfs"]:
        if "delta_pp" in e:
            print(
                f"[{e['symbol']}] HARD {e['action']} {e['delta_pp']:+.2f}pp "
                f"(target {e['target_weight_pct']:.1f}%, benefit {e['benefit_bps']}bps "
                f"vs cost {e['cost_bps']}bps) reasons={e['reasons']}"
            )
        else:
            print(
                f"[{e['symbol']}] HARD {e['action']} reasons={e['reason_codes']} "
                f"({e['no_action_reason']})"
            )
        print(
            f"      FACE (non-authoritative, NOT in plan): "
            f"crowd={e['crowd_consensus']} vs engine={e['engine_posture']} "
            f"-> divergence={e['divergence_bucket']}"
        )

    fin = result["finops"]
    print("\n--- Ledgers (kept strictly separate) ---")
    print(
        f"FinOps Ledger (business; NOT ETF investment P&L): "
        f"revenue={fin['revenue']} cost={fin['cost']} gross_margin={fin['gross_margin']}"
    )
    for r in fin["refused"]:
        print(f"  REFUSED SPEND: {r['reason']}")
    moves = "; ".join(
        f"{e['symbol']} {e['action']} {e['delta_pp']:+.2f}pp" for e in result["portfolio"]
    )
    print(f"Portfolio Ledger (SIMULATED allocation, no orders): {moves}")
    ex = result["experiment"]
    print(
        f"Experiment Ledger: run_id={ex['run_id']} seed={ex['seed']} "
        f"formula={ex['formula_version']}"
    )
    return 0


def cmd_desk(args: argparse.Namespace) -> int:
    symbols = args.symbols or ["0050", "0056", "00878"]
    result = build_pipeline_result(symbols, args.scenario, args.seed)
    html_text = render_desk_html(result)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")
    print(f"wrote {out}  ({len(html_text)} bytes) — open it in a browser")
    return 0


def cmd_journal(args: argparse.Namespace) -> int:
    """Append one dated research entry to the standing research journal.

    The "long-term plan": run on a schedule (Hermes cron / Task Scheduler) so the
    desk accumulates a memory of its own decisions over time. Deterministic — no
    LLM, no network — so it is reliable to schedule.
    """
    import datetime

    symbols = args.symbols or ["0050", "0056", "00878"]
    result = build_pipeline_result(symbols, args.scenario, args.seed)
    actions = []
    for e in result["etfs"]:
        a = {"symbol": e["symbol"], "action": e["action"]}
        if "delta_pp" in e:
            a["delta_pp"] = e["delta_pp"]
        else:
            a["reason"] = (e.get("reason_codes") or [""])[0]
        actions.append(a)
    entry = {
        "date": args.date or datetime.date.today().isoformat(),
        "scenario": args.scenario,
        "seed": args.seed,
        "actions": actions,
        "margin": result["finops"]["gross_margin"],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"journal += {entry['date']} (scenario={args.scenario}) -> {out}")
    return 0


def cmd_crowd(args: argparse.Namespace) -> int:
    book = load_databook_from_fixture(_fixtures_dir() / f"etf_{args.symbol}.json")
    seed = make_seed(book, market_scenario_label=args.scenario, rng_seed=args.seed)
    narrative = run_scenario(seed, n_personas=args.n, dry_run=args.dry_run)
    out = {
        "seed_id": narrative.seed_id,
        "artifact_type": narrative.artifact_type,
        "crowd_consensus": narrative.crowd_consensus,
        "non_authoritative": narrative.non_authoritative,
        "synthetic_population": narrative.synthetic_population,
        "n_personas": narrative.n_personas,
        "narrative_md": narrative.narrative_md,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    book = load_databook_from_fixture(_fixtures_dir() / f"etf_{args.symbol}.json")
    seed = make_seed(book, market_scenario_label=args.scenario, rng_seed=args.seed)
    a = run_scenario(seed, dry_run=True).crowd_consensus
    b = run_scenario(seed, dry_run=True).crowd_consensus
    ok = a == b
    print(f"determinism: crowd_consensus {a!r} == {b!r} -> {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


def cmd_fetch(args: argparse.Namespace) -> int:
    provider = SitcaFundamentals() if args.provider == "sitca" else None
    db = load_databook(
        args.symbol, live=args.live, fixtures_dir=_fixtures_dir(), fundamentals=provider
    )
    print(f"DataBook[{db.etf_symbol}] freshness={db.freshness}  observed_at={db.observed_at}")
    print(f"  book_hash={db.book_hash}  fundamentals_provider={args.provider}")
    for k, v in sorted(db.metrics.items()):
        print(f"  {k}: {v}")
    if db.freshness == "live":
        live = [f for f in (*LIVE_PRICE_FIELDS, *LIVE_MOMENTUM_FIELDS) if f in db.metrics]
        ref = sorted(f for f in db.metrics if f not in live)
        print(f"  [live: TWSE+Yahoo] {', '.join(live)}")
        print(f"  [reference: {args.provider}] {', '.join(ref)}")
    else:
        print(f"  [all reference: {args.provider}/fixture]")
    return 0


def cmd_finops(args: argparse.Namespace) -> int:
    from stackfund.l5_finops import stripe_client

    cap_remaining = 500.0
    receipts = None

    if args.live and stripe_client.is_configured():
        try:
            print("Stripe: LIVE (test mode) — creating real test-mode objects")
            earn = stripe_client.create_payment(299.0, "twd", "StackFund Pro subscription (test)")
            spend = stripe_client.create_payment(120.0, "twd", "SaaS/API provisioning (test)")
            cap_remaining -= 120.0
            receipts = [
                make_receipt(earn["id"], EARN, earn["status"], 299.0, "TWD", "Pro subscription"),
                make_receipt(spend["id"], SPEND, spend["status"], 120.0, "TWD", "provision tool"),
                # VoI cap refuses the next spend BEFORE any Stripe call (agency beat).
                attempt_spend("spend_refused", 999.0, cap_remaining),
            ]
        except Exception as exc:
            print(f"  Stripe LIVE failed: {type(exc).__name__}: {exc}  -> falling back to stub")
            receipts = None
            cap_remaining = 500.0

    if receipts is None:
        if args.live and not stripe_client.is_configured():
            print("Stripe: stub (no test key in secrets/stripe_secret_key.txt)")
        elif not args.live:
            print("Stripe: stub (pass --live for real Stripe test mode)")
        receipts = [
            record_earn("earn_001", 299.0),
            attempt_spend("spend_001", 120.0, cap_remaining),
            attempt_spend("spend_002", 999.0, cap_remaining - 120.0),
        ]

    pnl = operational_pnl("2026-06", receipts)
    fin = finops_ledger("run_finops", receipts, pnl)
    print(
        f"\nFinOps Ledger (business; NOT ETF investment P&L): "
        f"revenue={pnl.revenue} cost={pnl.cost} gross_margin={pnl.gross_margin}"
    )
    for r in fin.receipts:
        print(
            f"  {r.type:<14} {r.status:<10} {r.amount:>8.2f} {r.currency}  "
            f"id={r.receipt_id}  {r.reason or ''}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stackfund",
        description="StackFund Core-B: deterministic ENGINE + non-authoritative crowd FACE.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pipe = sub.add_parser("pipeline", help="run the full ENGINE pipeline over fixtures")
    p_pipe.add_argument("--symbols", nargs="*", help="ETF symbols (default: 0050 0056 00878)")
    p_pipe.add_argument("--scenario", default="升息")
    p_pipe.add_argument("--seed", type=int, default=42)
    p_pipe.add_argument("--json", action="store_true", help="emit the structured result as JSON")
    p_pipe.set_defaults(func=cmd_pipeline)

    p_desk = sub.add_parser(
        "desk", help="render the pipeline result as a self-contained static HTML"
    )
    p_desk.add_argument("--symbols", nargs="*", help="ETF symbols (default: 0050 0056 00878)")
    p_desk.add_argument("--scenario", default="升息")
    p_desk.add_argument("--seed", type=int, default=42)
    p_desk.add_argument("--out", default="dist/stackfund-desk.html", help="output HTML path")
    p_desk.set_defaults(func=cmd_desk)

    p_journal = sub.add_parser(
        "journal", help="append a dated research entry to the standing journal (the long-term plan)"
    )
    p_journal.add_argument("--symbols", nargs="*", help="ETF symbols (default: 0050 0056 00878)")
    p_journal.add_argument("--scenario", default="升息")
    p_journal.add_argument("--seed", type=int, default=42)
    p_journal.add_argument("--date", default="", help="ISO date (default: today)")
    p_journal.add_argument(
        "--out", default=".hermes-data/research-journal.jsonl", help="journal JSONL path"
    )
    p_journal.set_defaults(func=cmd_journal)

    p_crowd = sub.add_parser("crowd", help="run only the L3 crowd side-rail")
    p_crowd.add_argument("--symbol", default="0056")
    p_crowd.add_argument("--scenario", default="0056_cut")
    p_crowd.add_argument("--seed", type=int, default=42)
    p_crowd.add_argument("--n", type=int, default=30)
    p_crowd.add_argument("--dry-run", action="store_true", default=True)
    p_crowd.set_defaults(func=cmd_crowd)

    p_verify = sub.add_parser("verify", help="offline determinism check")
    p_verify.add_argument("--symbol", default="0056")
    p_verify.add_argument("--scenario", default="0056_cut")
    p_verify.add_argument("--seed", type=int, default=42)
    p_verify.set_defaults(func=cmd_verify)

    p_fetch = sub.add_parser("fetch", help="build a DataBook (frozen, or --live from TWSE)")
    p_fetch.add_argument("--symbol", default="0050")
    p_fetch.add_argument(
        "--live", action="store_true", help="overlay official TWSE daily price/volume"
    )
    p_fetch.add_argument(
        "--provider",
        choices=["fixture", "sitca"],
        default="fixture",
        help="fundamentals source (sitca is a documented stub -> falls back to fixture)",
    )
    p_fetch.set_defaults(func=cmd_fetch)

    p_finops = sub.add_parser(
        "finops", help="earn/spend/refused (stub, or --live real Stripe test mode)"
    )
    p_finops.add_argument(
        "--live", action="store_true", help="use real Stripe test key from secrets/"
    )
    p_finops.set_defaults(func=cmd_finops)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
