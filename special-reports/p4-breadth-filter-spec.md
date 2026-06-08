# P4 Breadth Filter Validation — Codex/Claude Code Spec

**Version**: v1.0 (Cowork, 2026-06-08)
**Builds on**: P1 main `8ac24c6` (Phase 1-3 merged). This is the validation of the ONE rule P1 left unverified — ATH-compression breadth filter (Phase 3 Q4: "inconclusive, gate never activated with only 2 ETF proxies").
**Hard rules**: research-only / protected file `7fc94586` unchanged / no Hanja / spec-vs-source conflict → stop and ask.

## Objective

P1 Phase 3 could not evaluate the ATH-compression breadth filter (`11→7→3`) because a 2-ETF proxy (QQQ/SPY) cannot define a shrinking new-ATH count. With a proper multi-name breadth dataset now available, test whether ATH-compression is a real leading-warning regime signal — and whether gating the scenario/Melt-Up/tier strategies on it improves drawdown and false-positive control after costs.

## Data (provided — do NOT synthesize)

- New cache committed at `data/raw/` from the P4 breadth package: 24 US single names + SPY/QQQ, 2019-01-02 → 2026-06-05, split+div adjusted, sha256-gated via `PROVENANCE.md`.
- Single-name universe (breadth basis): PLTR, NVDA, GOOGL, TSLA, META, MRVL, CLS, AMD, MSFT, TSM, INTC, ORCL, MU, AVGO, QCOM, AMAT, LRCX, KLAC, ARM, CRWD, SNOW, RKLB, WDC, SNDK.
- **Fail-closed**: verify each file's sha256 against PROVENANCE.md before use; abort on mismatch/missing. Reuse the Phase 3 integrity-gate pattern.
- IPO-staggered history is expected (ARM 2023-09, SNDK 2025-02, etc.) — the breadth universe grows over time; count new-ATHs only among names that have ≥252 trading days of history at each date (avoid an IPO printing a trivial "new ATH" on day 1).

## Breadth definition

For each trading day T, over the eligible single-name universe (≥252d history at T):
- `new_ath_count[T]` = number of names whose close[T] == running all-time-high[T].
- `compression[T]` = the new_ath_count sequence is "compressing" when it makes lower highs over a rolling window (e.g. 5 sessions): detect sequences like `11→7→3` and the generalizations `21→11→7`, `50→21→11` (parameterized, as Phase 2 already encodes).
- `breadth_regime[T]` ∈ {expansion, compression, washout(=0)} as a daily label.

**Preliminary in-sample observation (Cowork, must be reproduced and then stress-tested, NOT trusted as-is):** new-ATH count ran 10 / 10 / 9 / 3 / 0 over 2026-06-01..06-05, collapsing into the 6/5 crash. Phase 4 must determine whether this is a systematic leading signal or a single anecdote.

## Tasks

1. **Breadth feature module** — `new_ath_count`, compression detector, regime label. Unit-tested incl. the ≥252d eligibility rule and a reproduction test asserting the 6/1-6/5 sequence (10,10,9,3,0).
2. **Leading-signal study** — for every date, measure forward index (SPY/QQQ) returns over 1/3/5/10/20 sessions conditioned on breadth_regime. Question: does `compression` / `washout` precede negative forward returns and elevated drawdown more than the base rate? Report with bootstrap CIs; flag overfitting (one bull-dominated sample, few washout events).
3. **Re-evaluate the Phase 2/3 breadth filter** — now wire the real `new_ath_count` (not the 2-ETF proxy) into the existing `breadth_filter.py` gate on scenario_full, Melt-Up, and buy&hold. Compare gated vs ungated Sharpe / maxDD / Calmar after 5 bps costs. This finally answers Phase 3 Q4.
4. **Crash-window case studies** — quantify breadth behavior into the named events (2026-06-05 MU/SOX crash; 2022 drawdown if covered) — did compression lead, coincide, or lag?
5. **Report** `reports/p4_breadth_filter.md` — verdict on the breadth filter (keep/modify/reject as a regime gate), with the same evidence-limitation discipline as Phase 3 (single source, tech-heavy, bull-dominated, washout n small).

## Acceptance criteria

- Breadth cache sha256-verified (fail-closed); protected file untouched; no Hanja.
- Breadth computed on eligible-universe basis (no IPO day-1 false ATH).
- 6/1-6/5 (10,10,9,3,0) reproduction test passes.
- Gated-vs-ungated comparison reported for ≥3 strategies after costs → Phase 3 Q4 resolved.
- Forward-return-by-regime table with bootstrap CIs + explicit overfitting/limitation caveats.
- 1-command run; deterministic under the pinned env (numpy 2.2.6 / pandas 2.3.3).

## Non-goals

- No live trading / order generation. No claim breadth predicts future crashes from one in-sample episode. No canon change to framework v2 (breadth is a market-regime overlay, not a v2 single-name rule).
