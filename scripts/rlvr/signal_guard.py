#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""signal_guard.py — the learning-signal degeneracy breaker (#773 Gate C).

Contract: docs/architecture/rl-signal-contract.md §3. Five consecutive
identical settlement credits = a dead signal: freeze the posterior-moving
legs and raise the ``signal_degenerate`` blocker. Recovery is manual —
learning on a dead signal must not resume by itself (resuming on noise
is learning on noise).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEGENERATE_WINDOW = 5
STORE_REL = Path("runs") / "posterior-store.jsonl"


def check_degeneracy(credits: list[float],
                     window: int = DEGENERATE_WINDOW) -> dict:
    """The last ``window`` credits all identical -> degenerate. Numeric
    values only (non-numeric entries are ignored, never counted)."""
    vals = [float(c) for c in credits
            if isinstance(c, (int, float))][-window:]
    distinct = len(set(vals))
    degenerate = len(vals) >= window and distinct == 1
    return {"degenerate": degenerate, "distinct": distinct,
            "values": vals}


def recent_credits(ws: Path, n: int = DEGENERATE_WINDOW) -> list[float]:
    """The most recent settled credits from the ws posterior store
    (chronologic, oldest first), for the degeneracy check."""
    store = Path(ws) / "runs" / "posterior-store.jsonl"
    if not store.is_file():
        return []
    vals: list[float] = []
    for line in store.read_text(encoding="utf-8",
                                errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        c = rec.get("credit")
        if isinstance(c, (int, float)):
            vals.append(float(c))
    return vals[-n:]


def freeze_if_degenerate(ws: Path, credits: list[float],
                         window: int = DEGENERATE_WINDOW) -> bool:
    """True = the caller MUST skip the posterior-moving legs (the signal
    is dead). Raises the ``signal_degenerate`` blocker event when firing
    (kunglao_log; a telemetry failure prints, never raises)."""
    verdict = check_degeneracy(credits, window)
    if not verdict["degenerate"]:
        return False
    try:
        from kunglao_log import emit
        emit(Path(ws), "hook:signal_guard", "signal_degenerate",
             detail=json.dumps(verdict, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 — loud print, never raise
        print(f"signal_guard: blocker emit failed ({exc!r})",
              file=sys.stderr, flush=True)
    return True
