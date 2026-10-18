#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""devkit/spec_coverage.py — change specs must cite invariants and carry
an integration contract (#772).

openspec validate checks format and spec-implementation alignment. It
cannot check COVERAGE: whether the change spec reaches the system
property it should serve, and whether it answers the wiring question
(who calls the new face, when, with what firing fingerprint). This gate
adds those two checks inside the devkit:

For every OPEN change under openspec/changes/ (an open change has at
least one unchecked box in tasks.md):

  1. invariant citations — the change (proposal/design/specs/tasks)
     cites at least one invariant id from devkit/invariants/registry.json
     (INV-NNN).
  2. integration contract — the change's design.md (or proposal.md when
     no design exists) contains an "Integration contract" section
     naming the caller, the trigger timing, and the firing fingerprint.

Exit 1 with the violation list; 0 when no open change violates. A
completed change (all boxes checked) is historical and skipped.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGES = ROOT / "openspec" / "changes"
REGISTRY = Path(__file__).resolve().parent / "invariants" / "registry.json"
CONTRACT_HEADING = re.compile(
    r"^#{1,3}\s*integration\s+contract\b", re.IGNORECASE | re.MULTILINE)
INV_ID = re.compile(r"\bINV-\d{3}\b")
BOX_OPEN = re.compile(r"^\s*- \[ \]", re.MULTILINE)


def _open_changes(changes_dir: Path) -> list[Path]:
    out = []
    if not changes_dir.is_dir():
        return out
    for d in sorted(changes_dir.iterdir()):
        tasks = d / "tasks.md"
        if d.is_dir() and tasks.is_file() and BOX_OPEN.search(
                tasks.read_text(encoding="utf-8")):
            out.append(d)
    return out


def check_change(change: Path, valid_ids: set[str]) -> list[str]:
    name = change.name
    violations: list[str] = []
    texts = [p.read_text(encoding="utf-8", errors="replace")
             for p in sorted(change.rglob("*.md"))]
    joined = "\n".join(texts)
    cited = set(INV_ID.findall(joined))
    unknown = cited - valid_ids
    if not cited:
        violations.append(f"{name}: no invariant citation (INV-NNN) in any "
                          f"change doc — which system property does this "
                          f"change serve?")
    elif unknown:
        violations.append(f"{name}: unknown invariant ids "
                          f"{sorted(unknown)} — not in "
                          f"devkit/invariants/registry.json")
    design = change / "design.md"
    target = design if design.is_file() else change / "proposal.md"
    body = target.read_text(encoding="utf-8", errors="replace") \
        if target.is_file() else ""
    if not CONTRACT_HEADING.search(body):
        violations.append(
            f"{name}: no 'Integration contract' section in "
            f"{target.name} — who calls the new face, when, and with "
            f"what firing fingerprint?")
    return violations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--changes-dir", default=str(CHANGES))
    ap.add_argument("--registry", default=str(REGISTRY))
    args = ap.parse_args(argv)
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    valid_ids = {i["id"] for i in registry["invariants"]}
    open_changes = _open_changes(Path(args.changes_dir))
    violations: list[str] = []
    for change in open_changes:
        violations.extend(check_change(change, valid_ids))
    if not open_changes:
        print("spec coverage: no open changes — nothing to check")
        return 0
    for v in violations:
        print(f"  [FAIL] {v}")
    print(f"spec coverage: {len(violations)} violation(s) across "
          f"{len(open_changes)} open change(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
