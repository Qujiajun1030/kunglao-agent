#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""devkit/escape_rate.py — the Defect Escape Rate KPI, automated (#772).

Feeds the KPI that devkit/docs/defect_escape_rate.md designed in v0.1
and that stayed TBD for two months: defects that ESCAPE to production
(filed after the release tag) over all bugs of the release cycle.

    uv run python devkit/escape_rate.py --release v0.1.6-rc2 \
        --tag-date 2026-10-18            # compute + print the row
    ... --append                         # write the row into the doc

Uses `gh issue list --label bug` (post-release-bug label optional and
additive). Pure computation is a testable function; gh is only touched
in the fetch face.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DOC = Path(__file__).resolve().parent / "docs" / "defect_escape_rate.md"


def fetch_bug_issues(repo: str | None = None) -> list[dict]:
    cmd = ["gh", "issue", "list", "--label", "bug", "--state", "all",
           "--limit", "500", "--json", "number,title,createdAt,labels"]
    if repo:
        cmd += ["-R", repo]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def compute_rate(issues: list[dict], tag_date: str,
                 since: str | None = None) -> dict:
    """Cycle partition: a bug belongs to the cycle when created >=
    `since` (the cycle start); within it, pre = created < tag_date,
    post = created >= tag_date. Without `since`, the cycle is ALL
    history (documented caveat: prefer a cycle start). Numbers only —
    no gh here."""
    tag = datetime.fromisoformat(tag_date).replace(tzinfo=timezone.utc)
    start = (datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
             if since else None)
    pre = post = 0
    post_numbers: list[int] = []
    for it in issues:
        created = datetime.fromisoformat(
            it["createdAt"].replace("Z", "+00:00"))
        if start is not None and created < start:
            continue
        if created < tag:
            pre += 1
        else:
            post += 1
            post_numbers.append(int(it["number"]))
    total = pre + post
    rate = round(post / total * 100, 1) if total else None
    return {"release_total": total, "pre": pre, "post": post,
            "escape_rate": rate, "escaped_issues": post_numbers}


def doc_row(release: str, tag_date: str, r: dict) -> str:
    rate = r["escape_rate"]
    rate_s = "TBD" if rate is None else f"{rate}%"
    return (f"### {release} (tag {tag_date})\n"
            f"- Pre-release bug issues: {r['pre']}\n"
            f"- Post-release bug issues: {r['post']}"
            f" (#{'; #'.join(str(n) for n in r['escaped_issues']) or '-'})\n"
            f"- Escape rate: {rate_s}\n"
            f"- Notes: automated row (devkit/escape_rate.py)\n")


def append_row(release: str, row: str, doc: Path = DOC) -> None:
    text = doc.read_text(encoding="utf-8")
    if f"### {release} " in text:
        start = text.index(f"### {release} ")
        end = text.find("\n### ", start)
        end = len(text) if end == -1 else end + 1
        text = text[:start] + row + "\n" + text[end:]
    else:
        text = text.rstrip("\n") + "\n\n" + row
    doc.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--release", required=True)
    ap.add_argument("--tag-date", required=True,
                    help="YYYY-MM-DD of the release tag push")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--since", default=None,
                    help="YYYY-MM-DD cycle start (bugs created earlier "
                         "are out of the cycle's denominator)")
    ap.add_argument("--append", action="store_true",
                    help="write the row into docs/defect_escape_rate.md")
    args = ap.parse_args(argv)
    issues = fetch_bug_issues(args.repo)
    r = compute_rate(issues, args.tag_date, args.since)
    row = doc_row(args.release, args.tag_date, r)
    print(row, end="")
    if args.append:
        append_row(args.release, row)
        print(f"appended to {DOC}")
    if r["escape_rate"] is not None and r["escape_rate"] > 10.0:
        print("ESCAPE RATE > 10% — docs/defect_escape_rate.md's own rule "
              "fires: the next cycle's gate MUST add a regression test "
              "per escaped defect.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
