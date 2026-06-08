#!/usr/bin/env python3
"""1-command entry point for the P1 Framework Backtest Lab (spec L329).

Examples:
    python run.py                      # offline synthetic source (default)
    python run.py --source yfinance    # live daily bars (needs network)
    python run.py --symbols MU,GOOGL --start 2020-01-01 --end 2025-12-31

Research-only. This tool does not place, route, or recommend live trades.
"""

from __future__ import annotations

import argparse
import sys

from backtest_lab.config import RunConfig, UNIVERSE, DEFAULT_START, DEFAULT_END
from backtest_lab.pipeline import run_pipeline
from backtest_lab.integrity import IntegrityError


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="P1 Framework Backtest Lab (research-only)")
    p.add_argument("--source", default="synthetic", choices=["synthetic", "yfinance", "polygon"])
    p.add_argument("--symbols", default=",".join(UNIVERSE), help="comma-separated tickers")
    p.add_argument("--start", default=DEFAULT_START)
    p.add_argument("--end", default=DEFAULT_END)
    p.add_argument("--slippage-bps", type=float, default=5.0)
    p.add_argument("--commission", type=float, default=0.0)
    p.add_argument("--results-dir", default="results")
    p.add_argument("--cache-dir", default="cache")
    p.add_argument("--earnings-csv", default=None)
    p.add_argument("--phase3", action="store_true",
                   help="run the Phase 3 real-data analysis + report (source=csv cache)")
    p.add_argument("--phase4", action="store_true",
                   help="run the Phase 4 breadth-filter validation + report")
    args = p.parse_args(argv)

    if args.phase4:
        from backtest_lab.phase4 import run_phase4
        from backtest_lab.data.provenance import ProvenanceError
        try:
            rep = run_phase4(results_dir=args.results_dir)
        except (IntegrityError, ProvenanceError) as exc:
            print(f"[FAIL-CLOSED] {exc}", file=sys.stderr)
            return 2
        print("=== P1 Framework Backtest Lab — Phase 4 complete ===")
        for k, v in rep.items():
            print(f"  {k}: {v}")
        return 0

    if args.phase3:
        from backtest_lab.phase3 import run_phase3
        from backtest_lab.data.provenance import ProvenanceError
        try:
            rep = run_phase3(results_dir=args.results_dir)
        except (IntegrityError, ProvenanceError) as exc:
            print(f"[FAIL-CLOSED] {exc}", file=sys.stderr)
            return 2
        print("=== P1 Framework Backtest Lab — Phase 3 complete ===")
        for k, v in rep.items():
            print(f"  {k}: {v}")
        return 0

    cfg = RunConfig(
        symbols=[s.strip() for s in args.symbols.split(",") if s.strip()],
        start=args.start,
        end=args.end,
        source=args.source,
        slippage_bps=args.slippage_bps,
        commission=args.commission,
        results_dir=args.results_dir,
        cache_dir=args.cache_dir,
        earnings_csv=args.earnings_csv,
    )

    try:
        report = run_pipeline(cfg)
    except IntegrityError as exc:
        print(f"[FAIL-CLOSED] {exc}", file=sys.stderr)
        return 2

    print("=== P1 Framework Backtest Lab — run complete ===")
    for k, v in report.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
