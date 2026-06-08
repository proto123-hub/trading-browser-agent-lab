# P1 Phase 4 — Breadth Dataset Provenance

- Source: yfinance auto_adjust=True | yfinance 1.4.1 | fetched 2026-06-08T11:37:57.827658
- Universe: 24 US single names + 2 benchmarks (SPY/QQQ) = 26 files
- Period: 2019-01-02 ~ 2026-06-05 daily (shorter for late IPOs: ARM 2023-09, SNOW 2020-09, PLTR 2020-09, RKLB 2020-11, SNDK 2025-02, CRWD 2019-06)
- Adjustment: split+dividend adjusted, uniform (no mixing).
- KR names (SK Hynix/Samsung) intentionally excluded — different calendar/currency; breadth computed on US session only.

## Cross-validation vs vault-verified closes
AVGO 6/4 418.91 OK / GOOGL 6/4 372.19 OK / MRVL 6/2 290.79 OK / MU 6/4 996.00 OK / MU 6/5 864.01 OK — 5/5 exact

## Live breadth signal (new-ATH count/day, 24 single names) — preliminary, in-sample
2026-06-01: 10 / 06-02: 10 / 06-03: 9 / 06-04: 3 / 06-05: 0 (crash day)
=> compression 9->3->0 collapsed INTO the 6/5 crash. This is the exact pattern the ATH-compression
   filter targets; Phase 4 must test whether it leads crashes systematically (not one anecdote).

## Files (sha256 first 16)
- data/raw/PLTR.csv — 1427 rows, 2020-09-30..2026-06-05, single, sha256 b5a66a3b2141264a
- data/raw/NVDA.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 6c7280c0bfa19d1f
- data/raw/GOOGL.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 8034f5bb429e76f6
- data/raw/TSLA.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 c3aa4794067524ea
- data/raw/META.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 5bc8c37c4c7f5bfc
- data/raw/MRVL.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 8851afc81383aea8
- data/raw/CLS.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 d753676dc2e5fe72
- data/raw/AMD.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 d2bd2b2aa8541da3
- data/raw/MSFT.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 b8fb59218322c5cf
- data/raw/TSM.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 9e122ac8f0df534a
- data/raw/INTC.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 664d25684a0fad16
- data/raw/ORCL.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 d2c07ea416917c2e
- data/raw/MU.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 54d66eff7fd940ab
- data/raw/AVGO.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 8f4a4d1c6d08aa13
- data/raw/QCOM.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 7c956a4186b3cc71
- data/raw/AMAT.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 7315a15ab4b78ddf
- data/raw/LRCX.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 5bb605a42526ac22
- data/raw/KLAC.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 57ed45ec08fd9d31
- data/raw/ARM.csv — 684 rows, 2023-09-14..2026-06-05, single, sha256 58274573caa2607a
- data/raw/CRWD.csv — 1756 rows, 2019-06-12..2026-06-05, single, sha256 34d39845e1524082
- data/raw/SNOW.csv — 1437 rows, 2020-09-16..2026-06-05, single, sha256 7622164b0bb08928
- data/raw/RKLB.csv — 1388 rows, 2020-11-24..2026-06-05, single, sha256 4e46e149438a80ff
- data/raw/WDC.csv — 1867 rows, 2019-01-02..2026-06-05, single, sha256 e296511ad04493ec
- data/raw/SNDK.csv — 329 rows, 2025-02-13..2026-06-05, single, sha256 0edbd0055c5e1ad1
- data/raw/SPY.csv — 1867 rows, 2019-01-02..2026-06-05, benchmark, sha256 976be6b153e11eec
- data/raw/QQQ.csv — 1867 rows, 2019-01-02..2026-06-05, benchmark, sha256 af3dba146dd90ae4

## Upload (Daniel): repo -> Add file -> Upload files -> drag 'data' folder + this PROVENANCE.md -> commit to main.
Claude Code verifies each sha256 before use (fail-closed), same gate as Phase 3.