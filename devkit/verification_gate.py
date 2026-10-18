#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""devkit/verification_gate.py — Done means live-verified (#772).

"实际跑样本才算，不是你说做了就是事实" as a gate: a PR that changes
behavior must carry a Verification block in its body — a fenced command
plus its real output — before it can merge. This gate checks PRESENCE
and SHAPE (a command in a fence); executing the command stays with CI
or the reviewer.

    uv run python devkit/verification_gate.py --pr 765
    uv run python devkit/verification_gate.py --body-file pr.md

Exit 0 = verification block present with at least one fenced command;
exit 1 = missing/empty (with the exact remediation); 2 = usage error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

HEADING = re.compile(r"^#{1,3}\s*verification\b", re.IGNORECASE |
                     re.MULTILINE)
FENCE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)


def fetch_body(pr: int, repo: str | None = None) -> str:
    cmd = ["gh", "pr", "view", str(pr), "--json", "body",
           "--jq", ".body"]
    if repo:
        cmd += ["-R", repo]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return out.stdout


def check_body(body: str) -> tuple[bool, str]:
    m = HEADING.search(body)
    if not m:
        return False, ("no '## Verification' section — a behavior-"
                       "changing PR must carry one: the command you ran "
                       "plus its real output, fenced")
    section = body[m.end():]
    nxt = re.search(r"^#{1,3}\s", section, re.MULTILINE)
    section = section[:nxt.start()] if nxt else section
    commands = [c.strip() for c in FENCE.findall(section)
                if c.strip() and not c.strip().startswith("- [")]
    if not commands:
        return False, ("the Verification section has no fenced command — "
                       "add the exact command(s) whose output proves the "
                       "behavior")
    for c in commands:
        first = c.splitlines()[0]
        if first.startswith(("#", "//")):
            return False, ("the first Verification line is a comment — "
                           "put the command itself first")
    return True, f"{len(commands)} verification command(s) present"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pr", type=int)
    src.add_argument("--body-file", type=Path)
    ap.add_argument("--repo", default=None)
    args = ap.parse_args(argv)
    if args.pr is not None:
        body = fetch_body(args.pr, args.repo)
    else:
        body = args.body_file.read_text(encoding="utf-8")
    ok, why = check_body(body)
    print(f"verification gate: {why}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
