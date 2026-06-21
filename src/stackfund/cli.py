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
from stackfund.l1_databook import load_databook_from_fixture, make_seed
from stackfund.l2_scorecard import build_scorecard
from stackfund.l3_crowd import run_scenario
from stackfund.l4_portfolio import build_rebalance_plan
from stackfund.l5_finops import attempt_spend, operational_pnl, record_earn
from stackfund.l6_audit import crowd_report_provenance, decision_provenance
from stackfund.ledgers import experiment_ledger, finops_ledger, portfolio_ledger
from stackfund.report import compose_divergence


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


def cmd_pipeline(args: argparse.Namespace) -> int:
    symbols = args.symbols or ["0050", "0056", "00878"]
    portfolio = _load_portfolio()
    policy = PolicySet()
    costs = CostModel()
    market = MarketState(session="closed", as_of="2026-06-19")
    run_id = f"run_{args.seed}"

    receipts = [record_earn("earn_001", 299.0)]  # one Pro subscription (test-mode earn)
    cap_remaining = 500.0
    plans = []

    print(f"=== StackFund pipeline (scenario={args.scenario!r}, seed={args.seed}) ===")
    for sym in symbols:
        book = load_databook_from_fixture(_fixtures_dir() / f"etf_{sym}.json")
        scorecard = build_scorecard(book)
        state = AuthoritativeState(scorecard, portfolio, policy, costs, market)
        plan = build_rebalance_plan(state)  # ENGINE: AuthoritativeState only, never FACE
        decision_provenance(plan)
        plans.append(plan)

        # FACE side-rail (dry-run): narrative only; divergence computed at report time.
        seed = make_seed(book, market_scenario_label=args.scenario, rng_seed=args.seed)
        narrative = run_scenario(seed, dry_run=True)
        divergence = compose_divergence(narrative, scorecard)
        crowd_report_provenance(narrative, divergence)

        if plan.deltas:
            d = plan.deltas[0]
            print(
                f"[{sym}] HARD {plan.action} {d.hard_delta_pp:+.2f}pp "
                f"(target {d.target_weight_pct:.1f}%, benefit {d.benefit_bps}bps "
                f"vs cost {d.cost_bps}bps) reasons={list(d.hard_reasons)}"
            )
        else:
            print(
                f"[{sym}] HARD {plan.action} reasons={list(plan.reason_codes)} "
                f"({plan.no_action_reason})"
            )
        print(
            f"      FACE (non-authoritative, NOT in plan): "
            f"crowd={divergence.crowd_consensus} vs engine={divergence.engine_posture} "
            f"-> divergence={divergence.divergence_bucket}"
        )

    # FinOps SPEND + REFUSED SPEND beat (the business, not ETFs)
    receipts.append(attempt_spend("spend_001", 120.0, cap_remaining))
    cap_remaining -= 120.0
    receipts.append(attempt_spend("spend_002", 999.0, cap_remaining))  # breaches cap -> refused
    pnl = operational_pnl("2026-06", receipts)

    fin = finops_ledger(run_id, receipts, pnl)
    port = portfolio_ledger(run_id, plans)
    exp = experiment_ledger(
        run_id, parent_run_id="none", rng_seed=args.seed, scenario_label=args.scenario
    )

    print("\n--- Ledgers (kept strictly separate) ---")
    print(
        f"FinOps Ledger (business; NOT ETF investment P&L): "
        f"revenue={fin.pnl.revenue} cost={fin.pnl.cost} gross_margin={fin.pnl.gross_margin}"
    )
    for r in fin.receipts:
        if r.type == "refused_spend":
            print(f"  REFUSED SPEND: {r.reason}")
    moves = "; ".join(f"{e.etf_symbol} {e.action} {e.simulated_delta_pp:+.2f}pp" for e in port)
    print(f"Portfolio Ledger (SIMULATED allocation, no orders): {moves}")
    print(
        f"Experiment Ledger: run_id={exp.run_id} seed={exp.rng_seed} formula={exp.formula_version}"
    )
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
    p_pipe.set_defaults(func=cmd_pipeline)

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

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
