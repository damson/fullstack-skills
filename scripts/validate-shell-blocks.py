#!/usr/bin/env python3
"""Parse-check every shell block this marketplace publishes.

A skill's shell block is the part a reader pastes into a terminal. A block that
cannot even parse is not a typo in prose: it is a step that cannot be followed,
and one shipped green because nothing here read the shell it publishes.

`bash -n` parses without executing, so this never runs a skill's commands.

Placeholders are not errors. `git fetch <url> <branch>` is how these skills tell
a reader what to substitute, and bash reads `<url>` as a redirect, so every such
block would fail an unmodified parse. Each `<name>` token is replaced with a
plain word first; what survives is a real syntax error -- an unbalanced quote,
an unterminated loop, a `case` with no `esac`.

Usage:
  python3 scripts/validate-shell-blocks.py              # every plugin here
  python3 scripts/validate-shell-blocks.py <dir>        # one tree

Exits non-zero if any block fails, after reporting all of them.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# A fence opens on its own line, so a ``` appearing inside a line of code -- a
# regex matching mermaid fences, say -- does not close the block early.
FENCE = re.compile(r"^(\s*)```(\w*)\s*$")

# `<name>`, `<owner>/<repo>`, `<commit-to-drop>`. Anchored to a letter so that
# process substitution `<(...)`, here-strings `<<<`, and `<!doctype` are left
# alone, and confined to one line so a `->` further down cannot close a match
# that a `<` opened above it.
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]*>")

SHELL_LANGS = {"bash", "sh", "shell"}


def iter_blocks(text: str):
    """Yield (line number of the opening fence, dedented code) per shell block."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        opening = FENCE.match(lines[i])
        if not opening:
            i += 1
            continue
        indent, lang = opening.group(1), opening.group(2)
        body: list[str] = []
        j = i + 1
        while j < len(lines) and not FENCE.match(lines[j]):
            body.append(lines[j])
            j += 1
        if lang in SHELL_LANGS:
            strip = len(indent)
            yield i + 1, "\n".join(
                line[strip:] if line[:strip].isspace() else line for line in body
            )
        i = j + 1


def parse_error(code: str) -> str | None:
    """Return bash's complaint about `code`, or None when it parses."""
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as handle:
        handle.write(PLACEHOLDER.sub("PLACEHOLDER", code))
        path = handle.name
    try:
        done = subprocess.run(
            ["bash", "-n", path], capture_output=True, text=True, check=False
        )
    finally:
        Path(path).unlink(missing_ok=True)
    if done.returncode == 0:
        return None
    # bash prefixes each line with the temp file's name, which says nothing.
    complaint = done.stderr.strip().splitlines()
    return "; ".join(line.split(": ", 1)[-1] for line in complaint) or "does not parse"


def check(root: Path) -> int:
    sources = sorted(root.glob("plugins/*/skills/*/*.md")) or sorted(root.glob("**/*.md"))
    blocks = failures = 0
    for source in sources:
        for lineno, code in iter_blocks(source.read_text()):
            blocks += 1
            complaint = parse_error(code)
            if complaint is None:
                continue
            failures += 1
            rel = source.relative_to(root) if source.is_relative_to(root) else source
            print(f"✘ {rel}:{lineno} — {complaint}", file=sys.stderr)
            print(f"    {code.strip().splitlines()[0][:76]}", file=sys.stderr)
    if failures:
        print(f"\n✘ {failures} of {blocks} shell block(s) do not parse", file=sys.stderr)
        return 1
    print(f"✔ {blocks} shell block(s) parse under bash -n")
    return 0


if __name__ == "__main__":
    sys.exit(check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent))
