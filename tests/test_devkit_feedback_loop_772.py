# -*- coding: utf-8 -*-
"""tests/test_devkit_feedback_loop_772.py — the development mechanism's
feedback edge, as executable acceptance (issue #772).

Covers: the fingerprint spec's shape, the liveness gate in both
directions (a LIVE fixture workspace passes; an empty workspace — the
ctf-1 2026-10-18 shape, zero admissions and zero posterior movement —
must read RED), the verification and deferral gates' verdicts, the
escape-rate partition math, the invariant registry's cross-references,
and Gate 10's registration.

All fixtures are SYNTHETIC (privacy rule).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEVKIT = ROOT / "devkit"
for p in (str(ROOT), str(DEVKIT)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, DEVKIT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def lg():
    return _load("liveness_gate")


def _live_ws(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    logs = ws / "runs" / "logs"
    logs.mkdir(parents=True)
    (ws / "runs" / "strategy-log.jsonl").write_text(
        json.dumps({"event": "dispatch", "strategy": "sampled",
                    "claim": "C-001"}) + "\n", encoding="utf-8")
    (logs / "kunglao-2026-10-18.jsonl").write_text(
        json.dumps({"action": "dispatch", "admitted": ["dispatch/C-001"],
                    "claim": "C-001"}) + "\n" +
        json.dumps({"action": "task_terminal_settlement",
                    "claim": "C-001"}) + "\n", encoding="utf-8")
    (ws / "runs" / "posterior-store.jsonl").write_text(
        json.dumps({"schema": "posterior-store/1", "arm": "method:static"})
        + "\n", encoding="utf-8")
    cases = ws / "oracle" / "cases"
    cases.mkdir(parents=True)
    (cases / "case-001.yaml").write_text(
        "channel: repl\nhypothesis_ref: H-001\nupdate_map: {}\n",
        encoding="utf-8")
    return ws


def test_fingerprints_schema_and_seeds():
    fps = json.loads(
        (DEVKIT / "liveness_fingerprints.json").read_text(encoding="utf-8"))
    assert fps["schema"] == "liveness-fingerprints/1"
    assert len(fps["fingerprints"]) >= 5
    ids = {f["id"] for f in fps["fingerprints"]}
    assert {"rl-sampler-exit", "rl-admission-consumed",
            "rl-posterior-moved"} <= ids


def test_liveness_ledger_green_on_live_fixture(lg, tmp_path):
    rc = lg.run_ledger(_live_ws(tmp_path))
    assert rc == 0


def test_liveness_ledger_red_on_decorative_workspace(lg, tmp_path):
    """The ctf-1 2026-10-18 shape: ledgers exist but zero admissions,
    zero posterior movement, default strategy — the gate MUST read
    this as RED (exit 1), never as a silent skip."""
    ws = tmp_path / "ws"
    logs = ws / "runs" / "logs"
    logs.mkdir(parents=True)
    (ws / "runs" / "strategy-log.jsonl").write_text(
        json.dumps({"event": "dispatch", "strategy": "default",
                    "claim": "C-001"}) + "\n", encoding="utf-8")
    (logs / "kunglao-2026-10-18.jsonl").write_text(
        json.dumps({"action": "tick"}) + "\n", encoding="utf-8")
    rc = lg.run_ledger(ws)
    assert rc == 1


def test_liveness_missing_ledger_is_fail_not_skip(lg, tmp_path):
    ws = tmp_path / "empty-ws"
    ws.mkdir()
    rc = lg.run_ledger(ws)
    assert rc == 1


def test_verification_gate_verdicts():
    vg = _load("verification_gate")
    good = vg.check_body("## Summary\nx\n\n## Verification\n\n```\n"
                         "uv run pytest tests/x.py\n```\n")
    assert good[0]
    bad = vg.check_body("## Summary\nno verification section\n")
    assert not bad[0] and "Verification" in bad[1]
    empty = vg.check_body("## Verification\n\nnothing fenced\n")
    assert not empty[0] and "fenced" in empty[1]


def test_deferral_guard_verdicts():
    dg = _load("deferral_guard")
    ok_none = dg.check_body("a plain body", [])
    assert ok_none[0]
    bad = dg.check_body("the executor lands later in a follow-up", [])
    assert not bad[0] and "linked issue" in bad[1]
    ok_linked = dg.check_body("the executor lands later",
                              ["#773"])
    assert ok_linked[0]


def test_escape_rate_partition():
    er = _load("escape_rate")
    issues = [
        {"createdAt": "2026-10-17T10:00:00Z", "number": 1},
        {"createdAt": "2026-10-19T10:00:00Z", "number": 2},
        {"createdAt": "2026-10-01T10:00:00Z", "number": 3},
    ]
    r = er.compute_rate(issues, "2026-10-18", since="2026-10-15")
    assert r == {"release_total": 2, "pre": 1, "post": 1,
                 "escape_rate": 50.0, "escaped_issues": [2]}


def test_invariant_registry_cross_references():
    inv = json.loads((DEVKIT / "invariants" / "registry.json")
                     .read_text(encoding="utf-8"))
    assert inv["schema"] == "invariants/1"
    assert len(inv["invariants"]) >= 8
    fps = json.loads((DEVKIT / "liveness_fingerprints.json")
                     .read_text(encoding="utf-8"))
    fp_ids = {f["id"] for f in fps["fingerprints"]}
    for i in inv["invariants"]:
        if i.get("fingerprint") is not None:
            assert i["fingerprint"] in fp_ids, i["id"]


def test_gate10_registered_in_gates():
    qg = _load("quality_gates")
    assert 10 in qg.GATES
    assert qg.GATES[10][0] == "Liveness"


def test_spec_coverage_flags_open_change_without_contract(
        tmp_path, monkeypatch):
    sc = _load("spec_coverage")
    changes = tmp_path / "changes" / "issue-900-example"
    changes.mkdir(parents=True)
    (changes / "tasks.md").write_text("- [ ] do the thing\n",
                                      encoding="utf-8")
    (changes / "proposal.md").write_text(
        "a proposal citing INV-001 but no contract section\n",
        encoding="utf-8")
    violations = sc.check_change(changes, {"INV-001"})
    assert any("Integration contract" in v for v in violations)
    assert not any("invariant citation" in v for v in violations)
