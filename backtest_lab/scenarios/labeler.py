"""Canonical scenario labeler A-D (event-based, cloud-color-specific).

This module is the FIX-1 deliverable (spec L105-137, framework v2 L37-63):
the four scenarios are *events* (cloud-color transitions), not generic regime
states. Every fired predicate is logged with the bar date via
:func:`scenario_events`.

Scenario definitions (spec L109-135):
  A  Bearish-cloud breakthrough success: bearish cloud, then close holds above
     cloud top for 2 consecutive closes (LONG signal). [v2 L41, L88]
  B  Bullish-cloud breakdown: bullish cloud with price previously above, then
     close holds below cloud bottom for 2 consecutive closes. [v2 L42, L113-117]
  C  Failed breakthrough: one close above a bearish-cloud top followed by a
     close back inside the cloud; fake-breakout sub-label if attempt volume is
     below the 20-day average. [v2 L43, L48-51]
  D  Bullish-cloud continuation: price above a bullish cloud (HOLD/accumulate).
     [v2 L44]

All labels are computed from data available at or before the bar (no lookahead):
the confirmation completes on the bar it is reported.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ScenarioConfig:
    confirm_days: int = 2          # 2 consecutive daily closes (v2 L41, L88)
    fake_vol_mult: float = 1.0     # attempt volume below 20d avg => fake (v2 L50)


def consecutive(cond: pd.Series, n: int) -> pd.Series:
    """True at bar T iff ``cond`` is True for each of the last ``n`` bars."""
    c = cond.fillna(False).astype("float64")
    return c.rolling(n).sum().eq(float(n))


def label_scenarios(
    feats: pd.DataFrame, config: ScenarioConfig | None = None
) -> pd.DataFrame:
    """Return a boolean frame of fired scenario events aligned to ``feats``."""
    cfg = config or ScenarioConfig()
    n = cfg.confirm_days

    above = feats["above_cloud"].fillna(False)
    below = feats["below_cloud"].fillna(False)
    in_cloud = feats["in_cloud"].fillna(False)
    bearish = feats["bearish_cloud"].fillna(False)
    bullish = feats["bullish_cloud"].fillna(False)

    # --- Scenario A: bearish-cloud breakthrough, 2-day close hold above top ---
    held_above = consecutive(above, n)
    # the bar before the n-day window was not above the cloud (genuine entry)
    pre_not_above = ~above.shift(n).fillna(False)
    # cloud was bearish going into the breakout
    pre_bearish = bearish.shift(n).fillna(False)
    scenario_a = held_above.fillna(False) & pre_not_above & pre_bearish

    # --- Scenario B: bullish-cloud breakdown, 2-day close hold below bottom ---
    held_below = consecutive(below, n)
    pre_not_below = ~below.shift(n).fillna(False)
    pre_bullish = bullish.shift(n).fillna(False)
    pre_above = above.shift(n).fillna(False)  # price previously above cloud
    scenario_b = held_below.fillna(False) & pre_not_below & pre_bullish & pre_above

    # --- Scenario C: failed breakthrough (above bearish cloud, then back in) ---
    prev_above_bearish = (above.shift(1) & bearish.shift(1)).fillna(False)
    scenario_c = prev_above_bearish & in_cloud
    # fake-breakout sub-label: the attempt bar's volume was below 20d average
    attempt_vol_mult = feats["vol_mult"].shift(1)
    scenario_c_fake = scenario_c & (attempt_vol_mult < cfg.fake_vol_mult).fillna(False)

    # --- Scenario D: bullish-cloud continuation ---
    scenario_d = above & bullish

    out = pd.DataFrame(index=feats.index)
    out["scenario_a"] = scenario_a
    out["scenario_b"] = scenario_b
    out["scenario_c"] = scenario_c
    out["scenario_c_fake"] = scenario_c_fake
    out["scenario_d"] = scenario_d
    return out


# predicates worth logging alongside each fired event (spec L107)
_PREDICATE_COLS = [
    "close", "cloud_top", "cloud_bottom", "bearish_cloud", "bullish_cloud",
    "above_cloud", "below_cloud", "in_cloud", "rsi_wilder_14", "vol_mult",
    "tenkan_gt_kijun", "sma200",
]


def scenario_events(
    feats: pd.DataFrame, labels: pd.DataFrame, symbol: str
) -> pd.DataFrame:
    """Long-form log of every fired scenario with the bar date and predicates."""
    rows = []
    pred_cols = [c for c in _PREDICATE_COLS if c in feats.columns]
    scen_cols = [c for c in labels.columns if c.startswith("scenario_")]
    for date, lab in labels.iterrows():
        for scen in scen_cols:
            if bool(lab[scen]):
                row = {"date": date, "symbol": symbol, "scenario": scen}
                for col in pred_cols:
                    row[col] = feats.at[date, col]
                rows.append(row)
    return pd.DataFrame(rows)


def rebreakthrough_score(
    feats: pd.DataFrame,
    first_attempt: pd.Timestamp,
    second_attempt: pd.Timestamp,
    consolidation_low: float | None = None,
) -> dict:
    """Score the 5 re-breakthrough checks (spec L125-131, framework v2 L54-60).

    Returns a dict with each check's boolean result, the total score, and the
    sizing verdict: >=4/5 -> full size (stronger than first attempt);
    <=3/5 -> max 50% size.
    """
    f1 = feats.loc[first_attempt]
    f2 = feats.loc[second_attempt]

    # 1. Support: volume-confirmed bullish candle near SMA50/SMA200 (v2 L56).
    #    Proxy: second attempt close above SMA50 or SMA200 with vol_mult >= 1.0.
    near_sma = (f2["close"] >= f2["sma50"]) or (f2["close"] >= f2["sma200"])
    check_support = bool(near_sma and (f2["vol_mult"] >= 1.0))

    # 2. Volume: second-attempt volume >= +30% vs first attempt (v2 L57).
    check_volume = bool(f2["vol_mult"] >= f1["vol_mult"] * 1.30)

    # 3. Cloud thinning: thickness >= 20% smaller than first attempt (v2 L58).
    check_cloud = bool(f2["cloud_thickness"] <= f1["cloud_thickness"] * 0.80)

    # 4. Bullish RSI divergence: price low >= first-fail low while RSI higher.
    if consolidation_low is None:
        consolidation_low = f1["close"]
    check_divergence = bool(
        (f2["close"] >= consolidation_low) and (f2["rsi_wilder_14"] > f1["rsi_wilder_14"])
    )

    # 5. Tenkan > Kijun (v2 L60).
    check_tk = bool(f2["tenkan_gt_kijun"])

    checks = {
        "support": check_support,
        "volume": check_volume,
        "cloud_thinning": check_cloud,
        "rsi_divergence": check_divergence,
        "tenkan_gt_kijun": check_tk,
    }
    score = sum(checks.values())
    verdict = "full_size" if score >= 4 else "max_50pct_size"  # v2 L62-63
    return {"checks": checks, "score": score, "verdict": verdict}
