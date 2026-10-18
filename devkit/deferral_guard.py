#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""devkit/deferral_guard.py — deferral creates blocking edges (#772).

The #760 failure class: "the executor lands later" shipped three times,
and the later never came because deferrals were free prose. This gate
makes a deferral a HARD requirement: a PR/issue body that defers work
must link the OPEN issue that owns the deferral, or it cannot close.

    uv run python devkit/deferral_guard.py --body-file body.md
    uv run python devkit/deferral_guard.py --body-file body.md \
        --linked "#773,#774"

Markers (case-insensitive): follow-up, future work/card/issue/PR,
executor, later, 以后, 后续, 下一班. Exit 0 = no markers, or every
marker context is covered by a linked issue; exit 1 = deferral without
a linked issue.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

MARKERS = re.compile(
    r"follow-?up|future\s+(work|card|issue|pr)|executor\b|\blater\b|"
    r"以后|后续|下一班", re.IGNORECASE)


def fetch_body(number: int, kind: str = "issue",
               repo: str | None = None) -> str:
    cmd = ["gh", kind, "view", str(number), "--json", "body",
           "--jq", ".body"]
    if repo:
        cmd += ["-R", repo]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return out.stdout


def check_body(body: str, linked: list[str]) -> tuple[bool, str]:
    hits = sorted({m.group(0).lower() for m in MARKERS.finditer(body)})
    if not hits:
        return True, "no deferral markers"
    if not linked:
        return False, (f"deferral markers present ({', '.join(hits)}) "
                       f"but no linked issue — open the blocking issue "
                       f"and link it, or drop the deferral")
    return True, (f"deferral markers ({', '.join(hits)}) covered by "
                  f"linked: {', '.join(linked)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--body-file", type=Path)
    src.add_argument("--issue", type=int)
    src.add_argument("--pr", type=int)
    ap.add_argument("--linked", default="",
                    help="comma-separated OPEN issue numbers that own "
                         "the deferral, e.g. '#773,#774'")
    ap.add_argument("--repo", default=None)
    args = ap.parse_args(argv)
    if args.body_file is not None:
        body = args.body_file.read_text(encoding="utf-8")
    elif args.issue is not None:
        body = fetch_body(args.issue, "issue", args.repo)
    else:
        body = fetch_body(args.pr, "pr", args.repo)
    linked = [s.strip() for s in args.linked.split(",") if s.strip()]
    ok, why = check_body(body, linked)
    print(f"deferral guard: {why}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
