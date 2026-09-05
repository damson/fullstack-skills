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
from typing import NamedTuple

# A fence opens on its own line, so a ``` appearing inside a line of code -- a
# regex matching mermaid fences, say -- does not close the block early.
#
# Markdown fences are three or more backticks OR three or more tildes, and a
# block closes only on the same character, at least as long, carrying no info
# string. A checker that recognises only the exact three-backtick form does not
# report the others as bad: it skips them, and reports success for a file it
# never read.
OPENING = re.compile(r"^(\s*)(`{3,}|~{3,})[ \t]*([^`\s]*)[ \t]*$")
CLOSING = re.compile(r"^\s*(`{3,}|~{3,})[ \t]*$")

# `<name>`, `<owner>/<repo>`, `<commit-to-drop>`. Anchored to a letter so that
# process substitution `<(...)`, here-strings `<<<`, and `<!doctype` are left
# alone, and confined to one line so a `->` further down cannot close a match
# that a `<` opened above it.
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]*>")

SHELL_LANGS = {"bash", "sh", "shell"}


def closes(marker: str, line: str) -> bool:
    """True when `line` ends a block opened with `marker`."""
    closing = CLOSING.match(line)
    return bool(closing) and closing.group(1)[0] == marker[0] and len(closing.group(1)) >= len(marker)


class Block(NamedTuple):
    """One fenced block: where it opens, its dedented body, and its language."""

    line: int
    code: str
    lang: str
    closed: bool


def iter_blocks(text: str):
    """Yield a Block per shell block, plus any fence left unterminated.

    An unterminated fence is reported whatever its language: it swallows the
    rest of the document, so every shell block after it disappears from the
    walk, and the file passes for having nothing left to check.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        opening = OPENING.match(lines[i])
        if not opening:
            i += 1
            continue
        indent, marker, lang = opening.group(1), opening.group(2), opening.group(3)
        body: list[str] = []
        j = i + 1
        while j < len(lines) and not closes(marker, lines[j]):
            body.append(lines[j])
            j += 1
        closed = j < len(lines)
        if lang.lower() in SHELL_LANGS or not closed:
            strip = len(indent)
            yield Block(
                i + 1,
                "\n".join(line[strip:] if line[:strip].isspace() else line for line in body),
                lang.lower(),
                closed,
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
        for block in iter_blocks(source.read_text()):
            rel = source.relative_to(root) if source.is_relative_to(root) else source
            if not block.closed:
                failures += 1
                opened = f"{block.lang} fence" if block.lang else "fence"
                print(f"✘ {rel}:{block.line} — unterminated {opened}", file=sys.stderr)
                continue
            blocks += 1
            complaint = parse_error(block.code)
            if complaint is None:
                continue
            failures += 1
            print(f"✘ {rel}:{block.line} — {complaint}", file=sys.stderr)
            print(f"    {block.code.strip().splitlines()[0][:76]}", file=sys.stderr)
    if failures:
        checked = f"{blocks} shell block(s) checked" if blocks else "no shell block reached"
        print(f"\n✘ {failures} problem(s); {checked}", file=sys.stderr)
        return 1
    print(f"✔ {blocks} shell block(s) parse under bash -n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return check(Path(args[0]) if args else Path(__file__).resolve().parent.parent)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
