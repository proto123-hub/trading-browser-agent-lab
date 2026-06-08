# P1 Phase 4 — ATH-Compression Breadth Filter Validation

**Research-only.** Resolves P1 Phase 3 Q4 (breadth filter 'inconclusive — gate never activated with 2 ETF proxies'). No claim that breadth predicts future crashes from one in-sample episode (Non-Goals). Breadth is a market-regime overlay, not a v2 single-name rule.

- Breadth basis: 24 single names (>=252d eligibility), 26 cache files sha256-gated. Period 2019-01-02..2026-06-05.
- Regime day counts: {'neutral': 818, 'expansion': 339, 'compression': 281, 'warmup': 251, 'washout': 178}

## ⚠️ Evidence limitations

- Single source (yfinance), tech-heavy 24-name basis, **bull-dominated** sample; **few washout episodes** — any leading-signal result is fragile.
- Compression/washout labels are in-sample; no walk-forward selection.

## 1. Live breadth signal reproduced (6/1-6/5)

new-ATH count: {'2026-06-01': 10, '2026-06-02': 10, '2026-06-03': 9, '2026-06-04': 3, '2026-06-05': 0} -> regimes: {'2026-06-01': 'neutral', '2026-06-02': 'compression', '2026-06-03': 'compression', '2026-06-04': 'compression', '2026-06-05': 'washout'}.
First compression/washout day of the episode: **2026-06-02**; benchmark (SPY) forward returns from that day: {'fwd_1': -0.007, 'fwd_3': -0.029, 'fwd_5': nan, 'fwd_10': nan, 'fwd_20': nan, 'fwd_60': nan}.
The new-ATH count collapsed 9 -> 3 -> 0 **into** the 6/5 crash — compression led/coincided with the drawdown in this single episode.

## 2. Leading-signal study — SPY forward returns by breadth regime

| horizon | regime | mean fwd | 95% CI | n |
|---|---|---|---|---|
| 1d | ALL(base rate) | 0.0007 | [0.0001, 0.0013] | 1866 |
| 1d | expansion | 0.0011 | [0.0002, 0.0020] | 339 |
| 1d | compression | 0.0006 | [-0.0003, 0.0015] | 281 |
| 1d | washout | 0.0011 | [-0.0005, 0.0025] | 177 |
| 1d | neutral | 0.0004 | [-0.0007, 0.0015] | 818 |
| 1d | warmup | 0.0011 | [0.0002, 0.0020] | 251 |
| 3d | ALL(base rate) | 0.0021 | [0.0013, 0.0030] | 1864 |
| 3d | expansion | 0.0022 | [0.0006, 0.0038] | 339 |
| 3d | compression | 0.0031 | [0.0017, 0.0045] | 279 |
| 3d | washout | 0.0014 | [-0.0012, 0.0041] | 177 |
| 3d | neutral | 0.0016 | [-0.0002, 0.0032] | 818 |
| 3d | warmup | 0.0034 | [0.0018, 0.0050] | 251 |
| 5d | ALL(base rate) | 0.0036 | [0.0024, 0.0047] | 1862 |
| 5d | expansion | 0.0041 | [0.0023, 0.0059] | 339 |
| 5d | compression | 0.0041 | [0.0022, 0.0060] | 278 |
| 5d | washout | 0.0033 | [-0.0002, 0.0065] | 177 |
| 5d | neutral | 0.0026 | [0.0004, 0.0047] | 817 |
| 5d | warmup | 0.0055 | [0.0036, 0.0073] | 251 |
| 10d | ALL(base rate) | 0.0070 | [0.0055, 0.0086] | 1857 |
| 10d | expansion | 0.0071 | [0.0045, 0.0097] | 337 |
| 10d | compression | 0.0073 | [0.0045, 0.0100] | 276 |
| 10d | washout | 0.0033 | [-0.0016, 0.0075] | 177 |
| 10d | neutral | 0.0066 | [0.0036, 0.0095] | 816 |
| 10d | warmup | 0.0106 | [0.0080, 0.0130] | 251 |
| 20d | ALL(base rate) | 0.0139 | [0.0117, 0.0160] | 1847 |
| 20d | expansion | 0.0117 | [0.0074, 0.0158] | 337 |
| 20d | compression | 0.0113 | [0.0061, 0.0162] | 270 |
| 20d | washout | 0.0055 | [-0.0036, 0.0132] | 176 |
| 20d | neutral | 0.0155 | [0.0117, 0.0194] | 813 |
| 20d | warmup | 0.0205 | [0.0170, 0.0240] | 251 |
| 60d | ALL(base rate) | 0.0386 | [0.0353, 0.0420] | 1807 |
| 60d | expansion | 0.0363 | [0.0296, 0.0428] | 327 |
| 60d | compression | 0.0309 | [0.0228, 0.0382] | 261 |
| 60d | washout | 0.0250 | [0.0157, 0.0344] | 171 |
| 60d | neutral | 0.0458 | [0.0399, 0.0516] | 797 |
| 60d | warmup | 0.0364 | [0.0270, 0.0447] | 251 |

Read: if `compression`/`washout` rows show forward means below the `ALL(base rate)` row with non-overlapping CIs, breadth has leading value; overlapping CIs (likely, given few washout days) => not statistically established in-sample.

## 3. Q4 RESOLVED — gated vs ungated (real breadth gate, after 5bps)

| strategy | gate | CAGR | Sharpe | maxDD | Calmar | exposure |
|---|---|---|---|---|---|---|
| buy_and_hold | ungated | 0.4840 | 1.0785 | -0.5186 | 0.9019 | 0.9994 |
| buy_and_hold | gated | 0.2829 | 0.8028 | -0.4827 | 0.5767 | 0.7441 |
| scenario_full | ungated | 0.0087 | 0.2724 | -0.0234 | 4.6342 | 0.0055 |
| scenario_full | gated | 0.0058 | 0.1921 | -0.0321 | 2.9211 | 0.0035 |
| meltup_conflict_aware | ungated | 0.4145 | 1.0078 | -0.5008 | 0.7966 | 0.9972 |
| meltup_conflict_aware | gated | 0.2490 | 0.7634 | -0.4731 | 0.5214 | 0.7429 |

**The gate now ACTIVATES** (unlike the Phase 3 2-ETF proxy): gated rows differ from ungated — Phase 3 Q4 is answerable. Per-strategy conclusion (KEEP only if gated maxDD shallower AND Calmar not worse, after 5bps):

- **buy_and_hold**: gating maxDD -0.5186->-0.4827 (shallower: True), Calmar 0.9019->0.5767, Sharpe 1.0785->0.8028 => **REJECT (hard gate)**.
- **scenario_full**: gating maxDD -0.0234->-0.0321 (shallower: False), Calmar 4.6342->2.9211, Sharpe 0.2724->0.1921 => **REJECT (hard gate)**.
- **meltup_conflict_aware**: gating maxDD -0.5008->-0.4731 (shallower: True), Calmar 0.7966->0.5214, Sharpe 1.0078->0.7634 => **REJECT (hard gate)**.

Across all three, the gate trims drawdown only marginally while cutting Calmar/Sharpe materially — in this bull-dominated sample a hard breadth gate **does not pay for itself**.

## 4. Verdict — breadth filter as a regime gate

- The `11->7->3` compression pattern is now **computable and did fire** on the real 24-name basis (it was undefinable with 2 ETFs).
- In the one observable stress episode (6/5) compression **led/coincided** with the crash — encouraging but **n=1**.
- Systematic leading value: see the SPY/QQQ regime table — treat as **MODIFY/inconclusive** unless compression/washout CIs separate from base rate.
- **Recommendation:** keep breadth as a *risk-monitoring overlay* (washout = de-risk signal worth watching), but do NOT hard-gate strategies on it until validated across more washout episodes (2022 bear, out-of-sample).

---
*Generated by `python -m backtest_lab.phase4`. Deterministic under the pinned env; all inputs sha256-gated.*
