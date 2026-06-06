from __future__ import annotations

import pytest

from backtest_lab.integrity import (
    check_framework_source,
    assert_framework_source,
    IntegrityError,
    EXPECTED_SHA256_PREFIX,
    EXPECTED_LINES,
    EXPECTED_BYTES,
)


def test_framework_source_passes_gate():
    report = check_framework_source()
    assert report.exists
    assert report.ok, report.failures
    assert report.sha256_prefix == EXPECTED_SHA256_PREFIX
    assert report.n_lines == EXPECTED_LINES
    assert report.n_bytes == EXPECTED_BYTES
    assert report.n_lf == EXPECTED_LINES


def test_assert_raises_on_tampered_file(tmp_path):
    bad = tmp_path / "framework.md"
    bad.write_text("not the real framework\n")
    with pytest.raises(IntegrityError):
        assert_framework_source(bad)


def test_assert_raises_on_missing_file(tmp_path):
    with pytest.raises(IntegrityError):
        assert_framework_source(tmp_path / "does_not_exist.md")
