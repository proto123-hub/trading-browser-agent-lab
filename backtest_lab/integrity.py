"""Source-integrity gate for the framework v2 file.

Phase 0 / Phase 1 prerequisite (spec L85-86, L326): the pipeline must fail
*closed* if the canonical framework source is missing or does not match its
recorded fingerprint. No backtest is allowed to run against a tampered or
reconstructed source.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

# Canonical fingerprint of the protected framework source (CLAUDE.md section 4,
# spec L86). These values are intentionally hard-coded: they are the gate.
FRAMEWORK_V2_RELPATH = "special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md"
EXPECTED_SHA256_PREFIX = "7fc94586eb4b3a0c"
EXPECTED_LINES = 310
EXPECTED_LF_NEWLINES = 310
EXPECTED_BYTES = 16395


class IntegrityError(RuntimeError):
    """Raised when the framework source fails its integrity gate."""


@dataclass(frozen=True)
class IntegrityReport:
    path: Path
    exists: bool
    sha256: str
    sha256_prefix: str
    n_lines: int
    n_lf: int
    n_bytes: int
    ok: bool
    failures: tuple[str, ...]


def _repo_root() -> Path:
    # backtest_lab/integrity.py -> repo root is two parents up.
    return Path(__file__).resolve().parent.parent


def check_framework_source(path: str | Path | None = None) -> IntegrityReport:
    """Compute the integrity report for the framework v2 source.

    Does not raise; returns a report. Use :func:`assert_framework_source` to
    fail closed.
    """
    target = Path(path) if path is not None else _repo_root() / FRAMEWORK_V2_RELPATH
    failures: list[str] = []

    if not target.is_file():
        return IntegrityReport(
            path=target, exists=False, sha256="", sha256_prefix="",
            n_lines=0, n_lf=0, n_bytes=0, ok=False,
            failures=(f"source file missing: {target}",),
        )

    raw = target.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    prefix = digest[: len(EXPECTED_SHA256_PREFIX)]
    n_bytes = len(raw)
    n_lf = raw.count(b"\n")
    # "lines" counts LF-terminated lines; the source ends with a trailing LF so
    # n_lines == n_lf == 310.
    n_lines = n_lf

    if prefix != EXPECTED_SHA256_PREFIX:
        failures.append(f"sha256 prefix {prefix!r} != expected {EXPECTED_SHA256_PREFIX!r}")
    if n_lines != EXPECTED_LINES:
        failures.append(f"line count {n_lines} != expected {EXPECTED_LINES}")
    if n_lf != EXPECTED_LF_NEWLINES:
        failures.append(f"LF count {n_lf} != expected {EXPECTED_LF_NEWLINES}")
    if n_bytes != EXPECTED_BYTES:
        failures.append(f"byte count {n_bytes} != expected {EXPECTED_BYTES}")

    return IntegrityReport(
        path=target, exists=True, sha256=digest, sha256_prefix=prefix,
        n_lines=n_lines, n_lf=n_lf, n_bytes=n_bytes,
        ok=not failures, failures=tuple(failures),
    )


def assert_framework_source(path: str | Path | None = None) -> IntegrityReport:
    """Fail closed: raise :class:`IntegrityError` unless the source matches."""
    report = check_framework_source(path)
    if not report.ok:
        raise IntegrityError(
            "framework v2 source integrity gate FAILED:\n  - "
            + "\n  - ".join(report.failures)
        )
    return report
