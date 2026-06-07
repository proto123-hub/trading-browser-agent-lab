"""Provenance / sha256 gate for the committed real-data cache (Phase 3).

Parses ``PROVENANCE.md`` and verifies each ``data/raw/*.csv`` against its
recorded sha256 prefix. Fail-closed: the real-data pipeline must refuse to run
on a cache that does not match its provenance record (spec L79-86 data-quality
requirements extended to the committed cache).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


class ProvenanceError(RuntimeError):
    """Raised when a data file fails its provenance sha256 gate."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class FileProvenance:
    relpath: str
    sha256_prefix: str


def parse_provenance(path: str | Path | None = None) -> list[FileProvenance]:
    p = Path(path) if path is not None else _repo_root() / "PROVENANCE.md"
    if not p.is_file():
        raise ProvenanceError(f"PROVENANCE.md not found at {p}")
    text = p.read_text(encoding="utf-8")
    pairs = re.findall(r"(data/raw/[\w.]+).*?sha256 ([0-9a-f]{16})", text)
    if not pairs:
        raise ProvenanceError("no 'data/raw/*.csv ... sha256 <hex>' entries in PROVENANCE.md")
    return [FileProvenance(rel, sha) for rel, sha in pairs]


def verify_data_cache(
    provenance_path: str | Path | None = None,
    data_root: str | Path | None = None,
) -> dict[str, str]:
    """Fail-closed: verify every recorded file's sha256 prefix. Returns the
    verified {relpath: sha256_prefix} map or raises :class:`ProvenanceError`."""
    root = Path(data_root) if data_root is not None else _repo_root()
    records = parse_provenance(provenance_path)
    failures: list[str] = []
    verified: dict[str, str] = {}
    for rec in records:
        f = root / rec.relpath
        if not f.is_file():
            failures.append(f"missing: {rec.relpath}")
            continue
        got = hashlib.sha256(f.read_bytes()).hexdigest()[: len(rec.sha256_prefix)]
        if got != rec.sha256_prefix:
            failures.append(f"sha256 mismatch {rec.relpath}: {got} != {rec.sha256_prefix}")
        else:
            verified[rec.relpath] = rec.sha256_prefix
    if failures:
        raise ProvenanceError(
            "data cache provenance gate FAILED:\n  - " + "\n  - ".join(failures)
        )
    return verified
