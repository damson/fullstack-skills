#!/usr/bin/env python3
"""Assemble the inventory a release needs, from git.

Two audiences, one source:

  --since <tag>   notes for the published GitHub Release, describing what landed
                  on main since that tag (empty tag = the first release).
  --pr-body       body for the develop → main pull request, describing what is
                  about to land.

Both lead with the plugin version changes, because that is what a consumer of the
marketplace acts on: which plugins does `claude plugin update` now have work to do
for. The commit list is the supporting detail, not the headline.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r'"version"\s*:\s*"([^"]+)"')


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def version_at(ref, plugin):
    """The plugin's version at a git ref, or None if it did not exist there."""
    path = f"plugins/{plugin}/.claude-plugin/plugin.json"
    blob = git("show", f"{ref}:{path}") if ref else ""
    if not blob:
        return None
    match = VERSION.search(blob)
    return match.group(1) if match else None


def current_version(plugin):
    path = ROOT / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    try:
        return json.loads(path.read_text()).get("version")
    except (OSError, json.JSONDecodeError):
        return None


def plugins():
    return sorted(p.name for p in (ROOT / "plugins").iterdir() if p.is_dir())


def version_table(base_ref):
    """Rows for plugins whose version moved between base_ref and the worktree."""
    rows = []
    for name in plugins():
        was = version_at(base_ref, name) if base_ref else None
        now = current_version(name)
        if now is None:
            continue
        if was is None:
            rows.append(f"| `{name}` | — | {now} | new |")
        elif was != now:
            rows.append(f"| `{name}` | {was} | {now} | updated |")
    if not rows:
        return ["_No plugin versions changed._"]
    return [
        "| Plugin | Was | Now | |",
        "|---|---:|---:|---|",
        *rows,
    ]


def commits(rng):
    subjects = git("log", rng, "--no-merges", "--format=- %s") if rng else ""
    lines = [l for l in subjects.splitlines() if l.strip()]
    if not lines:
        return ["_No direct commits._"]
    shown = lines[:40]
    if len(lines) > len(shown):
        # Never truncate silently: a capped list reads as a complete one.
        shown.append(f"- …and {len(lines) - len(shown)} more")
    return shown


def merged_prs(rng):
    if not rng:
        return "(none)"
    merges = git("log", rng, "--merges", "--format=%s")
    found = re.findall(r"Merge pull request #(\d+) ", merges)
    return " ".join(f"#{n}" for n in found) if found else "(none — direct commits only)"


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--since", help="previous release tag; empty string for the first release")
    group.add_argument("--pr-body", action="store_true")
    args = parser.parse_args()

    if args.pr_body:
        base, head = "origin/main", "origin/develop"
        rng = f"{base}..{head}"
        stat = git("diff", "--shortstat", base, head) or "(no file changes)"
        out = [
            "## What is being released",
            "",
            *version_table(base),
            "",
            f"**Pull requests in this batch:** {merged_prs(rng)}",
            "",
            f"**Diffstat:** {stat}",
            "",
            "<details><summary>Commits</summary>",
            "",
            *commits(rng),
            "",
            "</details>",
            "",
            "---",
            "",
            "Opened automatically on the three-day release cadence, and set to "
            "merge itself once `validate` passes. Close it to hold the release; "
            "the next run will reopen it when the cadence comes round again.",
        ]
    else:
        tag = (args.since or "").strip()
        # No tag yet: the first release covers everything on the branch.
        rng = f"{tag}..HEAD" if tag else "HEAD"
        out = [
            *version_table(tag),
            "",
            f"**Pull requests:** {merged_prs(rng)}",
            "",
            "### Changes",
            "",
            *commits(rng),
        ]
        if tag:
            out += ["", f"_Since {tag}._"]

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
