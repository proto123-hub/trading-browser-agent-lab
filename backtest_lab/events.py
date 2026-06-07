"""Named-event injection (annotations only).

Loads ``events.yaml`` and exposes helpers to tag bar dates / event windows for
a symbol. This mechanism never modifies price data — it only annotates real
calendar dates so reports can flag named stress events (spec L206, L236).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml


@dataclass(frozen=True)
class NamedEvent:
    symbol: str
    date: pd.Timestamp
    kind: str
    label: str
    note: str = ""


def load_events(path: str | Path = "events.yaml") -> list[NamedEvent]:
    p = Path(path)
    if not p.exists():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: list[NamedEvent] = []
    for raw in data.get("named_events", []):
        out.append(
            NamedEvent(
                symbol=str(raw["symbol"]),
                date=pd.Timestamp(raw["date"]).tz_localize(None),
                kind=str(raw.get("kind", "unknown")),
                label=str(raw.get("label", "")),
                note=str(raw.get("note", "")),
            )
        )
    return out


def events_for(events: list[NamedEvent], symbol: str) -> list[NamedEvent]:
    return [e for e in events if e.symbol == symbol]


def event_window_flags(
    index: pd.DatetimeIndex,
    events: list[NamedEvent],
    symbol: str,
    pre: int = 5,
    post: int = 5,
) -> pd.DataFrame:
    """Boolean columns flagging exact event dates and +/- window membership.

    Only dates that exist in ``index`` are flagged exactly; window membership is
    by position so it works even if the precise date is a non-trading day.
    """
    out = pd.DataFrame(index=index)
    out["named_event"] = False
    out["named_event_window"] = False
    out["named_event_kind"] = ""
    for ev in events_for(events, symbol):
        # nearest index position at or after the event date
        pos = index.searchsorted(ev.date)
        if pos >= len(index):
            continue
        lo = max(0, pos - pre)
        hi = min(len(index) - 1, pos + post)
        out.iloc[lo : hi + 1, out.columns.get_loc("named_event_window")] = True
        if index[pos] == ev.date:
            out.iloc[pos, out.columns.get_loc("named_event")] = True
        out.iloc[pos, out.columns.get_loc("named_event_kind")] = ev.kind
    return out
