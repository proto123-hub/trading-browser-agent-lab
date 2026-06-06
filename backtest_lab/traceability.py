"""Line-level traceability from canonical spec rules to framework v2 source.

Phase 0 residual deliverable (spec L287, L302-306, L328): every canonical
threshold in the implementation spec is mapped back to the exact line range in
``special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md``. The mapping
below is the curated set of ``[v2 L..]`` tags from the spec; the generator
validates each range against the real file (fail-closed via the integrity gate)
and writes ``results/framework_v2_traceability.csv``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .integrity import assert_framework_source, _repo_root, FRAMEWORK_V2_RELPATH

# (spec_rule, framework_v2_line_start, framework_v2_line_end, notes)
# Line numbers reference the 310-line framework v2 source.
MAPPING: list[tuple[str, int, int, str]] = [
    ("cloud_color_definition", 10, 20, "bearish: Senkou A<B; bullish: A>B; price-position reads"),
    ("ichimoku_five_lines", 26, 33, "Tenkan9/Kijun26/SenkouA/SenkouB52/Chikou, +26 displacement"),
    ("scenarios_a_to_d_table", 37, 44, "event-based A-D cloud-color transitions (FIX-1)"),
    ("scenario_a_breakthrough", 41, 41, "bearish->above cloud + 2-day close hold = LONG"),
    ("scenario_b_breakdown", 42, 42, "bullish->below cloud + 2-day close hold = reduce/SHORT"),
    ("scenario_c_failed_breakout", 43, 43, "above bearish cloud then back inside = stand aside"),
    ("scenario_d_continuation", 44, 44, "price above bullish cloud = HOLD/accumulate"),
    ("scenario_c_detail", 48, 51, "1-day above then re-entry; sub-volume => fake breakout"),
    ("scenario_c_fake_volume", 50, 50, "attempt volume below 20d average => fake breakout"),
    ("rebreakthrough_five_checks", 54, 60, "support/volume/cloud-thinning/RSI-divergence/Tenkan>Kijun"),
    ("rebreakthrough_check_support", 56, 56, "vol-confirmed bullish candle at SMA50/200 after 3-5d base"),
    ("rebreakthrough_check_volume", 57, 57, "2nd-attempt volume >= +30% vs first attempt"),
    ("rebreakthrough_check_cloud", 58, 58, "cloud thickness >= 20% smaller than first attempt"),
    ("rebreakthrough_check_divergence", 59, 59, "price low >= first-fail low while RSI higher"),
    ("rebreakthrough_check_tenkan_kijun", 60, 60, "Tenkan > Kijun"),
    ("rebreakthrough_score_full", 62, 62, ">=4/5 => stronger LONG than first attempt"),
    ("rebreakthrough_score_half", 63, 63, "<=3/5 => max 50% sizing"),
    ("three_stage_engine", 67, 111, "3-stage accumulate/confirm/take-profit + immediate exits"),
    ("stage1_accumulation", 71, 82, "pre-entry accumulation block"),
    ("stage1_zone", 72, 75, "-3% to -5% below bearish-cloud top"),
    ("stage1_rsi", 76, 76, "Wilder RSI 45-55 (neutral)"),
    ("stage1_volume", 77, 77, "volume 1.0-1.3x of 20d average"),
    ("stage1_sma200_filter", 78, 78, "close above SMA200"),
    ("stage1_size", 79, 79, "25-50% of target"),
    ("stage1_stop", 80, 80, "SMA200 -7%"),
    ("stage2_confirmed_entry", 84, 95, "confirmed-entry block"),
    ("stage2_trigger", 88, 88, "2 consecutive daily closes above cloud top"),
    ("stage2_volume", 89, 89, "volume >= 1.5x of 20d average"),
    ("stage2_rsi", 90, 90, "RSI 55-70"),
    ("stage2_tenkan_kijun", 91, 91, "Tenkan > Kijun"),
    ("stage2_size", 92, 92, "add 25-50% (cumulative 75-100%)"),
    ("stage2_stop", 93, 93, "entry -7..-10% or SMA50 close break"),
    ("stage3_tiers", 97, 104, "tiered profit-taking 33/33/33"),
    ("stage3_tier1", 102, 102, "RSI>=75 OR +20% from entry"),
    ("stage3_tier2", 103, 103, "Bollinger upper +2 ATR OR +35% from entry"),
    ("stage3_tier3_trailing", 104, 104, "SMA50 close break (trailing)"),
    ("immediate_exits", 108, 111, "override-all immediate-exit rules"),
    ("immediate_exit_2day_below", 109, 109, "close below cloud top 2+ sessions => sell 50%"),
    ("immediate_exit_fake", 110, 110, "high-vol bearish candle below breakout => sell 100%"),
    ("immediate_exit_sma50", 111, 111, "SMA50 close break => trailing 33% exit"),
    ("scenario_b_ladder", 113, 117, "retail reduce ladder (no shorting)"),
    ("scenario_b_ladder_step1", 115, 115, "cloud-bottom -3% approach + RSI<50 => reduce 33%"),
    ("scenario_b_ladder_step2", 116, 116, "2-day close below cloud bottom => reduce further 33%"),
    ("scenario_b_ladder_step3", 117, 117, "SMA200 break => exit 100%"),
    ("rsi_wilder_standard", 123, 123, "Wilder 14d RSI is canonical (not Cutler)"),
    ("bollinger_band", 133, 136, "20d 2-sigma; upper +2ATR tier-2 trigger; SMA20 break"),
    ("atr_module", 138, 141, "ATR 14d module"),
    ("atr_stop", 139, 139, "entry -1.5 ATR"),
    ("atr_targets", 140, 140, "entry +3 ATR (t1) / +5 ATR (t2)"),
    ("atr_expansion_sizing", 141, 141, "ATR expansion => reduce size"),
]


def build_traceability(framework_path: str | Path | None = None) -> pd.DataFrame:
    """Validate each mapping against the framework source; return a frame.

    Runs the integrity gate first (fail-closed). For each rule, marks
    ``status`` = ``verified`` when the line range is in-bounds and non-empty,
    else ``out_of_range`` / ``empty_range``.
    """
    assert_framework_source(framework_path)
    path = Path(framework_path) if framework_path else _repo_root() / FRAMEWORK_V2_RELPATH
    lines = path.read_text(encoding="utf-8").splitlines()
    total = len(lines)

    rows = []
    for spec_rule, start, end, notes in MAPPING:
        if not (1 <= start <= end <= total):
            status = "out_of_range"
        else:
            snippet = "".join(lines[start - 1 : end]).strip()
            status = "verified" if snippet else "empty_range"
        rows.append(
            {
                "spec_rule": spec_rule,
                "framework_v2_line_start": start,
                "framework_v2_line_end": end,
                "status": status,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows, columns=[
        "spec_rule", "framework_v2_line_start", "framework_v2_line_end", "status", "notes",
    ])


def write_traceability(
    out_path: str | Path = "results/framework_v2_traceability.csv",
    framework_path: str | Path | None = None,
) -> Path:
    df = build_traceability(framework_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out
