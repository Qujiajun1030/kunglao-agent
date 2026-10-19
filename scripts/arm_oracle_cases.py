#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arm_oracle_cases.py — compile the intake anchors into armed oracle
cases (issue #773 W1: the reward source).

The 2026-10-18 live-workspace forensics found the learning loop's
reward source dead: `no armed oracle cases — case posteriors never
move`. The anchors were always collected at intake (goal_verbatim /
primary_questions / success_criterion / verification_method); this
compiler turns them into `oracle/cases/*.yaml` docs carrying ALL five
arming fields (settle_round_credit.CASE_ARMING_FIELDS), one case per
primary question, so every workspace that can be analyzed can also be
learned from.

    uv run python scripts/arm_oracle_cases.py --ws <workspace>

Idempotent: existing case files are never touched. Refuses (exit 1)
when the anchors are blank — a workspace that cannot produce a reward
source is not analyzable under RLVR. The expected face encodes the
DECLARED completion anchor (verdict=PASS by the declared method); the
oracle runner's own shape law stays the single gate for loadability.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

CASES_REL = Path("oracle") / "cases"
METHOD_TO_CHANNEL = {
    "reproduction": "replay",
    "replay-evidence": "replay",
    "replay": "replay",
    "static": "probe",
    "probe": "probe",
    "manual": "probe",
}


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def compile_cases(ws: Path) -> list[dict]:
    """Pure compiler: returns the case docs for this workspace (empty
    when the anchors are blank — the caller refuses)."""
    ws = Path(ws)
    spec = _load_yaml(ws / "task_spec.yaml")
    goal = _load_yaml(ws / "goal-operationalization.yaml")
    questions = [str(q).strip() for q in
                 (spec.get("primary_questions") or []) if str(q).strip()]
    method = str(spec.get("verification_method") or "").strip()
    criterion = str(spec.get("success_criterion") or "").strip() or \
        str(goal.get("goal_verbatim") or "").strip()
    if not questions or not criterion:
        return []
    channel = METHOD_TO_CHANNEL.get(method.lower(), "probe")
    acceptance = [str(a).strip() for a in
                  (goal.get("acceptance") or []) if str(a).strip()]
    cases = []
    for n, q in enumerate(questions, 1):
        evidence_ref = f"anchor:success_criterion[{n}]"
        cases.append({
            "id": f"case-pq-{n:02d}",
            "channel": channel,
            "target_pq": q,
            "hypothesis_ref": "H-001",
            "update_map": {"green_up": ["H-001"], "red_up": ["H-001"]},
            "expected": [{"field": "verdict", "value": "PASS",
                          "evidence_refs": [evidence_ref]}],
            "mutations": [{"kind": "omit", "target": evidence_ref}],
            "_criterion": criterion,
            "_acceptance": acceptance[:2],
        })
    return cases


def arm(ws: Path) -> tuple[int, str]:
    cases = compile_cases(ws)
    if not cases:
        return 1, ("anchors blank (no primary_questions or no success "
                   "criterion) — a workspace that cannot produce a "
                   "reward source is not analyzable under RLVR")
    out_dir = ws / CASES_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    written = skipped = 0
    for case in cases:
        out = out_dir / f"{case['id']}.yaml"
        if out.exists():
            skipped += 1
            continue
        doc = {k: v for k, v in case.items() if not k.startswith("_")}
        out.write_text(yaml.safe_dump(doc, allow_unicode=True,
                                      sort_keys=False), encoding="utf-8")
        written += 1
    return 0, (f"armed {written} oracle case(s) "
               f"({skipped} already present) in {CASES_REL}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ws", required=True)
    args = ap.parse_args(argv)
    rc, msg = arm(Path(args.ws))
    print(f"arm_oracle_cases: {msg}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
