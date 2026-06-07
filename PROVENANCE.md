# P1 Phase 3 Raw Data Provenance

- Source: yfinance auto_adjust=True (split+dividend adjusted)
- Fetched (UTC): 2026-06-07T06:26:41.337110 | yfinance 1.4.1
- Period: 2019-01-02 ~ 2026-06-05 daily (ARM: 2023-09-14 IPO~)
- Adjustment basis: split + dividend adjusted (uniform across all 9 files — no mixing).
  Note: nominal-level triggers (MU $950) run on adjusted series; recent bars match nominal
  within ~0.1% (post last ex-div). Historical tier events shift marginally — document in report.

## Cross-validation vs vault-verified closes (Polygon-verified project logs)
AVGO 6/4 418.91 OK / GOOGL 6/4 372.19 OK / MRVL 6/2 290.79 OK / MU 6/4 996.00 OK / MRVL 6/4 316.43 OK — 5/5 exact

## Files (sha256 first 16)
- data/raw/MU.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 3abd9daeebc2c420
- data/raw/AVGO.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 b7fba307a60d166b
- data/raw/MRVL.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 78198638c991575a
- data/raw/GOOGL.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 ebf62b42cf6e148b
- data/raw/NVDA.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 dc1799f6fa8f8d38
- data/raw/AMD.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 d2bd2b2aa8541da3
- data/raw/ARM.csv — 684 rows, 2023-09-14..2026-06-05, sha256 58274573caa2607a
- data/raw/QQQ.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 8b04ef9aac906946
- data/raw/SPY.csv — 1867 rows, 2019-01-02..2026-06-05, sha256 0f93bd320efb531e
- data/raw/earnings_dates.csv — 162 rows, 7 symbols, 2020-06..2026-09, sha256 57ff710830b39ccf
  Caveat: yfinance earnings calendar; dates may include estimates, timing=unknown for all.
  2019 earnings not covered — mark missing per spec. QQQ/SPY: no earnings (ETF).

## Upload instructions (Daniel)
1. repo main page -> Add file -> Upload files
2. Drag the entire local 'data' folder (structure data/raw/*.csv is preserved on folder drag)
3. Also drag this PROVENANCE.md (repo root) -> Commit directly to main
4. Claude Code verifies sha256 per file before use (fail-closed).