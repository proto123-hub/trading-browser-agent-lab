"""Canonical Scenario A-D strategy — 3-Stage entry/exit engine.

Traces to framework v2 L67-117 and spec L139-165, L225-231. Implemented as a
stateful, path-dependent simulator producing a fractional position series in
[0, 1] plus an auditable transaction log. Every transaction records the v2 line
it traces to.

Evaluation priority per bar (spec L162: "Immediate exits override all holds"):
  1. Immediate exits      (v2 L108-111): cloud-top 2-day break -> -50%;
                           high-volume bearish breakdown -> -100%.
  2. Stop loss            (v2 L80, L93): stage stop hit -> -100%.
  3. Scenario B ladder    (v2 L113-117): bullish-cloud breakdown reduction.
  4. Stage 3 tiers        (v2 L97-104): 33/33/33 profit-taking + SMA50 trailing.
  5. Entries              (v2 L71-95):  Stage 1 accumulation, Stage 2 confirmation.

Variants:
  - "full"        : stages 1+2+3, immediate exits, B ladder, C re-breakthrough cap.
  - "stage1_only" : Stage 1 accumulation only; exits via stop / immediate / ladder.
  - "stage2_only" : enter full target on Stage 2 confirmation (no pre-accumulation).

No-lookahead: all decisions at bar T use feature columns at T (cloud is the
displaced cloud projected to T) or earlier; execution lag is applied later by
the engine when the position series is backtested.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ..scenarios.labeler import label_scenarios, rebreakthrough_score, ScenarioConfig


@dataclass(frozen=True)
class ScenarioStrategyConfig:
    variant: str = "full"                 # full | stage1_only | stage2_only
    target_size: float = 1.0
    stage1_size: float = 0.40             # within 25-50% (v2 L79)
    stage1_approach_lo: float = 0.03      # -3% (v2 L72/L75)
    stage1_approach_hi: float = 0.05      # -5%
    stage1_rsi_lo: float = 45.0           # v2 L76
    stage1_rsi_hi: float = 55.0
    stage1_vol_lo: float = 1.0            # v2 L77
    stage1_vol_hi: float = 1.3
    stage1_stop_sma200_buf: float = 0.07  # SMA200 -7% (v2 L80)
    stage2_vol_min: float = 1.5           # v2 L89
    stage2_rsi_lo: float = 55.0           # v2 L90
    stage2_rsi_hi: float = 70.0
    stage2_stop_buf: float = 0.10         # entry -10% (v2 L93)
    tier1_rsi: float = 75.0               # v2 L102
    tier1_gain: float = 0.20
    tier2_atr_mult: float = 2.0           # BB upper + 2 ATR (v2 L103)
    tier2_gain: float = 0.35
    tier_fraction: float = 1.0 / 3.0      # 33/33/33 (v2 L98)
    immediate_below_days: int = 2         # v2 L109
    trailing_mode: str = "canonical_once"  # canonical_once | non_canonical_full (F2)
    stage2_stop_sma50: bool = False       # add SMA50-break to Stage 2 stop (v2 L93 "or", F4)
    b_approach: float = 0.03              # cloud-bottom -3% approach (v2 L115)
    b_rsi_max: float = 50.0
    b_reduce: float = 1.0 / 3.0
    rebreakthrough_lookback: int = 30     # bars to link a prior failed breakout


@dataclass
class _State:
    size: float = 0.0
    stage: int = 0
    stage2_entry: float = 0.0
    stop_price: float = 0.0
    t1: bool = False
    t2: bool = False
    t3: bool = False
    last_c_date: pd.Timestamp | None = None


def run_scenario_strategy(
    feats: pd.DataFrame,
    config: ScenarioStrategyConfig | None = None,
) -> tuple[pd.Series, pd.DataFrame, pd.Series]:
    """Return (position[0..1], transactions_df, entry_signal_bool)."""
    cfg = config or ScenarioStrategyConfig()
    labels = label_scenarios(feats, ScenarioConfig())
    idx = feats.index
    pos = pd.Series(0.0, index=idx)
    entry_signal = pd.Series(False, index=idx)
    st = _State()
    txns: list[dict] = []

    below_top_streak = 0
    below_bottom_streak = 0

    def record(date, action, delta, price, reason):
        txns.append({
            "date": date, "action": action, "size_delta": round(delta, 6),
            "price": float(price), "reason": reason,
            "position_after": round(st.size, 6),
        })

    def sell_fraction(date, frac_of_target, price, reason):
        amt = min(st.size, frac_of_target * cfg.target_size)
        if amt <= 1e-9:
            return
        st.size -= amt
        record(date, "SELL", -amt, price, reason)
        if st.size <= 1e-9:
            st.size = 0.0
            st.stage = 0
            st.t1 = st.t2 = st.t3 = False

    for date in idx:
        row = feats.loc[date]
        close = row["close"]
        cloud_top = row["cloud_top"]
        cloud_bottom = row["cloud_bottom"]
        sma50 = row["sma50"]
        sma200 = row["sma200"]
        rsi = row["rsi_wilder_14"]
        vol_mult = row["vol_mult"]
        atr = row.get("atr_14", float("nan"))
        bb_upper = row.get("bb_upper", float("nan"))

        # track scenario C for re-breakthrough linkage (full variant)
        if bool(labels.at[date, "scenario_c"]):
            st.last_c_date = date

        # streaks for 2-day rules
        above_top = pd.notna(cloud_top) and close > cloud_top
        below_top = pd.notna(cloud_top) and close < cloud_top
        below_bottom = pd.notna(cloud_bottom) and close < cloud_bottom
        below_top_streak = below_top_streak + 1 if below_top else 0
        below_bottom_streak = below_bottom_streak + 1 if below_bottom else 0

        if st.size > 0:
            # --- 1. Immediate exits (override all holds) ---
            # F1: v2 L110 fake-breakout = high-volume bearish candle whose close
            # is back below the *breakout level* (cloud top), and only after a
            # confirmed breakthrough (stage 2). Stage-1 accumulation is protected
            # by its own SMA200 -7% stop, not by this rule.
            if (st.stage == 2 and vol_mult >= cfg.stage2_vol_min and close < row["open"]
                    and pd.notna(cloud_top) and close < cloud_top):
                sell_fraction(date, 1.0, close, "immediate_exit_fake[v2 L110]")
            # close below cloud top for >= N sessions -> sell 50%
            elif below_top_streak >= cfg.immediate_below_days:
                sell_fraction(date, 0.5, close, "immediate_exit_2day_below[v2 L109]")

            # --- 2. Stop loss (F4: optional SMA50-break alternative, v2 L93) ---
            stop_hit = bool(st.stop_price) and close < st.stop_price
            if (cfg.stage2_stop_sma50 and st.stage == 2
                    and pd.notna(sma50) and close < sma50):
                stop_hit = True
            if st.size > 0 and stop_hit:
                sell_fraction(date, 1.0, close, "stop_loss[v2 L80/L93]")

            # --- 3. Scenario B ladder (bullish-cloud breakdown) ---
            if st.size > 0 and bool(row["bullish_cloud"]):
                if pd.notna(sma200) and close < sma200:
                    sell_fraction(date, 1.0, close, "scenario_b_sma200[v2 L117]")
                elif below_bottom_streak >= 2:
                    sell_fraction(date, cfg.b_reduce, close, "scenario_b_2day[v2 L116]")
                elif (pd.notna(cloud_bottom)
                      and 0 <= (close - cloud_bottom) / cloud_bottom <= cfg.b_approach
                      and rsi < cfg.b_rsi_max):
                    sell_fraction(date, cfg.b_reduce, close, "scenario_b_approach[v2 L115]")

            # --- 4. Stage 3 tiers (only with the full / stage2 engines) ---
            if st.size > 0 and cfg.variant != "stage1_only" and st.stage == 2:
                # T3 trailing: SMA50 close break. F2: canonical is a one-time 33%
                # trailing exit (v2 L104/L111), guarded by a once-flag. The
                # full-liquidation behaviour is kept as a labelled non-canonical
                # variant for comparison.
                if pd.notna(sma50) and close < sma50:
                    if cfg.trailing_mode == "non_canonical_full":
                        sell_fraction(date, 1.0, close, "stage3_tier3_trailing_full[non-canonical]")
                    elif not st.t3:
                        st.t3 = True
                        sell_fraction(date, cfg.tier_fraction, close, "stage3_tier3_trailing[v2 L104/L111]")
                if st.size > 0 and not st.t1 and (
                    rsi >= cfg.tier1_rsi or close >= st.stage2_entry * (1 + cfg.tier1_gain)
                ):
                    st.t1 = True
                    sell_fraction(date, cfg.tier_fraction, close, "stage3_tier1[v2 L102]")
                if st.size > 0 and not st.t2 and (
                    (pd.notna(bb_upper) and pd.notna(atr) and close >= bb_upper + cfg.tier2_atr_mult * atr)
                    or close >= st.stage2_entry * (1 + cfg.tier2_gain)
                ):
                    st.t2 = True
                    sell_fraction(date, cfg.tier_fraction, close, "stage3_tier2[v2 L103]")

        # --- 5. Entries ---
        # Stage 2 confirmed entry (scenario A + filters)
        stage2_ok = (
            bool(labels.at[date, "scenario_a"])
            and vol_mult >= cfg.stage2_vol_min
            and cfg.stage2_rsi_lo <= rsi <= cfg.stage2_rsi_hi
            and bool(row["tenkan_gt_kijun"])
        )
        if cfg.variant in ("full", "stage2_only") and stage2_ok and st.stage < 2:
            target = cfg.target_size
            # C re-breakthrough cap: if a recent failed breakout preceded this,
            # size <= 50% unless score >= 4/5 (v2 L62-63).
            if cfg.variant == "full" and st.last_c_date is not None:
                gap = idx.get_loc(date) - idx.get_loc(st.last_c_date)
                if 0 < gap <= cfg.rebreakthrough_lookback:
                    score = rebreakthrough_score(feats, st.last_c_date, date)
                    if score["verdict"] != "full_size":
                        target = min(target, 0.5 * cfg.target_size)
            add = max(0.0, target - st.size)
            if add > 1e-9:
                st.size += add
                st.stage = 2
                st.stage2_entry = close
                st.stop_price = close * (1 - cfg.stage2_stop_buf)
                record(date, "BUY", add, close, "stage2_confirmed[v2 L84-95]")
                entry_signal.at[date] = True

        # Stage 1 accumulation (full / stage1_only), only when flat
        elif cfg.variant in ("full", "stage1_only") and st.stage == 0 and st.size == 0:
            approach = (pd.notna(cloud_top)
                        and cfg.stage1_approach_lo <= (cloud_top - close) / cloud_top <= cfg.stage1_approach_hi)
            stage1_ok = (
                bool(row["bearish_cloud"]) and approach
                and cfg.stage1_rsi_lo <= rsi <= cfg.stage1_rsi_hi
                and cfg.stage1_vol_lo <= vol_mult <= cfg.stage1_vol_hi
                and pd.notna(sma200) and close > sma200
            )
            if stage1_ok:
                st.size = cfg.stage1_size
                st.stage = 1
                st.stage2_entry = close  # provisional reference for tiers if promoted
                st.stop_price = sma200 * (1 - cfg.stage1_stop_sma200_buf)
                record(date, "BUY", cfg.stage1_size, close, "stage1_accumulation[v2 L71-82]")
                entry_signal.at[date] = True

        pos.at[date] = st.size

    txn_df = pd.DataFrame(
        txns, columns=["date", "action", "size_delta", "price", "reason", "position_after"]
    )
    return pos, txn_df, entry_signal
