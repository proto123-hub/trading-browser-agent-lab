from __future__ import annotations

from backtest_lab.traceability import (
    build_traceability,
    MAPPING,
    PROXY_RULES,
    write_traceability,
)


def test_all_mappings_verified_or_proxy():
    df = build_traceability()
    assert len(df) == len(MAPPING)
    assert list(df.columns) == [
        "spec_rule", "framework_v2_line_start", "framework_v2_line_end", "status", "notes",
    ]
    # every canonical rule maps to a real line range: verified, or an explicitly
    # documented proxy (N3) -- never out_of_range/empty_range.
    assert df["status"].isin(["verified", "proxy"]).all(), df[~df["status"].isin(["verified", "proxy"])]
    proxy_rows = set(df.loc[df["status"] == "proxy", "spec_rule"])
    assert proxy_rows == set(PROXY_RULES)
    # proxy rows must carry the deviation note
    for _, r in df[df["status"] == "proxy"].iterrows():
        assert "PROXY" in r["notes"]


def test_line_ranges_in_bounds():
    df = build_traceability()
    assert (df["framework_v2_line_start"] >= 1).all()
    assert (df["framework_v2_line_end"] <= 310).all()
    assert (df["framework_v2_line_start"] <= df["framework_v2_line_end"]).all()


def test_write_traceability(tmp_path):
    out = write_traceability(tmp_path / "trace.csv")
    assert out.exists()
    text = out.read_text()
    assert "spec_rule" in text and "scenario_a_breakthrough" in text
