"""StackFund CLI — the composition root that wires ENGINE + FACE.

Subcommands:
  pipeline   run L1->L2->L4 (+L5 earn/spend/refused, +L6 P&L) over fixtures,
             with the L3 crowd FACE rendered as a non-authoritative side-rail.
  crowd      run only the L3 crowd side-rail for one ETF (dry-run by default).
  verify     offline determinism check: same seed -> same modifier.

Note: importing the crowd side-rail (L3) here is fine — the CLI is the
composition root. The firewall forbids *L4* from importing L3, not the CLI.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from stackfund.l1_databook import load_databook_from_fixture, make_seed
from stackfund.l2_scorecard import build_scorecard
from stackfund.l3_crowd import run_scenario
from stackfund.l4_portfolio import build_rebalance_plan
from stackfund.l5_finops import attempt_spend, operational_pnl, record_earn
from stackfund.l6_audit import crowd_report_provenance, decision_provenance


def _fixtures_dir() -> Path:
    override = os.environ.get("STACKFUND_FIXTURES")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "fixtures"


def cmd_pipeline(args: argparse.Namespace) -> int:
    symbols = args.symbols or ["0050", "0056", "00878"]
    receipts = [record_earn("earn_001", 299.0)]  # one Pro subscription (test-mode earn)
    cap_remaining = 500.0

    print(f"=== StackFund pipeline (scenario={args.scenario!r}, seed={args.seed}) ===")
    for sym in symbols:
        book = load_databook_from_fixture(_fixtures_dir() / f"etf_{sym}.json")
        scorecard = build_scorecard(book)
        plan = build_rebalance_plan(scorecard)  # ENGINE: hard-only, never sees crowd
        decision_provenance(plan)

        # FACE side-rail (dry-run): narrative + non-authoritative modifier only.
        seed = make_seed(book, market_scenario_label=args.scenario, rng_seed=args.seed)
        signal = run_scenario(seed, dry_run=True)
        crp = crowd_report_provenance(signal)

        if plan.deltas:
            d = plan.deltas[0]
            print(
                f"[{sym}] HARD action={plan.action} delta={d.hard_delta_pp:+.2f}pp "
                f"reasons={list(d.hard_reasons)}"
            )
        else:
            print(f"[{sym}] HARD action={plan.action} ({plan.no_action_reason})")
        print(
            f"      crowd (non-authoritative, NOT in plan): "
            f"modifier={signal.contrarian_modifier:+.2f} "
            f"is_authoritative={signal.is_authoritative} digest={crp.narrative_digest[:12]}"
        )

    # SPEND + REFUSED SPEND beat
    receipts.append(attempt_spend("spend_001", 120.0, cap_remaining))
    cap_remaining -= 120.0
    receipts.append(attempt_spend("spend_002", 999.0, cap_remaining))  # breaches cap -> refused

    pnl = operational_pnl("2026-06", receipts)
    print(
        f"\nOperational P&L {pnl.period}: revenue={pnl.revenue} cost={pnl.cost} "
        f"gross_margin={pnl.gross_margin}"
    )
    for r in receipts:
        if r.type == "refused_spend":
            print(f"  REFUSED SPEND: {r.reason}")
    return 0


def cmd_crowd(args: argparse.Namespace) -> int:
    book = load_databook_from_fixture(_fixtures_dir() / f"etf_{args.symbol}.json")
    seed = make_seed(book, market_scenario_label=args.scenario, rng_seed=args.seed)
    signal = run_scenario(seed, n_personas=args.n, dry_run=args.dry_run)
    out = {
        "seed_id": signal.seed_id,
        "contrarian_modifier": signal.contrarian_modifier,
        "is_authoritative": signal.is_authoritative,
        "n_personas": signal.n_personas,
        "formula_id": signal.formula_id,
        "narrative_md": signal.narrative_md,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    book = load_databook_from_fixture(_fixtures_dir() / f"etf_{args.symbol}.json")
    seed = make_seed(book, market_scenario_label=args.scenario, rng_seed=args.seed)
    a = run_scenario(seed, dry_run=True).contrarian_modifier
    b = run_scenario(seed, dry_run=True).contrarian_modifier
    ok = a == b
    print(f"determinism: {a:+.4f} == {b:+.4f} -> {'OK' if ok else 'FAIL'}")
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
