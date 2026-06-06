"""End-to-end Phase 1 pipeline (1-command, spec L329).

Steps:
  1. Fail-closed framework-source integrity gate.
  2. Write line-level traceability CSV.
  3. Load the universe (default: offline synthetic source), cache raw inputs.
  4. Compute features per symbol; cache derived features separately.
  5. Label canonical scenarios A-D; log every fired event with its date.
  6. Backtest the 5 baselines per symbol; aggregate metrics.
  7. Emit machine-readable result tables + run provenance.

Outputs reproducible from cached or declared data sources.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import RunConfig
from .integrity import assert_framework_source
from .traceability import write_traceability
from .data import load_universe
from .features import compute_features, load_earnings_csv
from .features.ath_breadth import compression_sequence
from .scenarios import label_scenarios, scenario_events
from .strategies import all_baselines, backtest_positions, ExecConfig
from .config import BREADTH_PROXIES


def run_pipeline(config: RunConfig | None = None) -> dict:
    cfg = config or RunConfig()
    results = Path(cfg.results_dir)
    results.mkdir(parents=True, exist_ok=True)
    feat_cache = Path(cfg.cache_dir) / "features"
    feat_cache.mkdir(parents=True, exist_ok=True)

    # 1. integrity gate (fail closed)
    integrity = assert_framework_source()

    # 2. traceability
    trace_path = write_traceability(results / "framework_v2_traceability.csv")

    # 3. data
    datasets = load_universe(
        cfg.symbols, cfg.start, cfg.end, source=cfg.source,
        cache_dir=str(Path(cfg.cache_dir) / "raw"),
    )

    earnings = None
    if cfg.earnings_csv:
        earnings = load_earnings_csv(cfg.earnings_csv)

    exec_cfg = ExecConfig(slippage_bps=cfg.slippage_bps, commission=cfg.commission)

    summary_rows = []
    event_frames = []
    provenance = {}
    closes = {}

    for sym, ds in datasets.items():
        provenance[sym] = ds.provenance.to_dict()
        sym_earn = None
        if earnings is not None:
            sym_earn = earnings.loc[earnings["symbol"] == sym, "date"]
        feats = compute_features(ds.frame, sym_earn)
        feats.to_csv(feat_cache / f"{sym}.csv")
        closes[sym] = ds.frame["close"]

        # scenarios
        labels = label_scenarios(feats)
        events = scenario_events(feats, labels, sym)
        if not events.empty:
            event_frames.append(events)

        # baselines
        for name, pos in all_baselines(ds.frame).items():
            res = backtest_positions(ds.frame, pos, exec_cfg)
            row = {"symbol": sym, "strategy": name, **res.metrics}
            row["scenario_a_count"] = int(labels["scenario_a"].sum())
            row["scenario_b_count"] = int(labels["scenario_b"].sum())
            row["scenario_c_count"] = int(labels["scenario_c"].sum())
            row["scenario_d_count"] = int(labels["scenario_d"].sum())
            summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(results / "summary.csv", index=False)

    if event_frames:
        all_events = pd.concat(event_frames, ignore_index=True)
    else:
        all_events = pd.DataFrame(columns=["date", "symbol", "scenario"])
    all_events.to_csv(results / "scenario_events.csv", index=False)

    # breadth compression on proxies (spec L209-213)
    proxy_syms = [s for s in BREADTH_PROXIES if s in closes]
    if len(proxy_syms) >= 2:
        proxy_close = pd.DataFrame({s: closes[s] for s in proxy_syms}).dropna()
        comp = compression_sequence(proxy_close, (11, 7, 3))
        comp.to_csv(results / "breadth_compression.csv")

    (results / "run_provenance.json").write_text(json.dumps(provenance, indent=2))

    report = {
        "integrity_ok": integrity.ok,
        "integrity_sha256_prefix": integrity.sha256_prefix,
        "n_symbols": len(datasets),
        "source": cfg.source,
        "n_scenario_events": int(len(all_events)),
        "traceability_csv": str(trace_path),
        "summary_csv": str(results / "summary.csv"),
        "scenario_events_csv": str(results / "scenario_events.csv"),
    }
    return report
