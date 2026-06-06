from __future__ import annotations

from backtest_lab.traceability import build_traceability, MAPPING, write_traceability


def test_all_mappings_verified():
    df = build_traceability()
    assert len(df) == len(MAPPING)
    assert list(df.columns) == [
        "spec_rule", "framework_v2_line_start", "framework_v2_line_end", "status", "notes",
    ]
    # every canonical rule must map to a real, non-empty line range
    assert (df["status"] == "verified").all(), df[df["status"] != "verified"]


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
