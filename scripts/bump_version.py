#!/usr/bin/env python3
"""Raise one plugin's patch version.

Edits the version string in place with a targeted substitution rather than
re-serialising the JSON: a round-trip through json.dump would reformat the whole
file and re-escape every non-ASCII character, burying a one-field change in a
whole-file diff.

Usage: scripts/bump_version.py <plugin-name>
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r'("version"\s*:\s*")(\d+)\.(\d+)\.(\d+)(")')


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2

    path = ROOT / "plugins" / sys.argv[1] / ".claude-plugin" / "plugin.json"
    if not path.is_file():
        print(f"No such plugin manifest: {path}", file=sys.stderr)
        return 1

    text = path.read_text()
    match = VERSION.search(text)
    if not match:
        # Anything but MAJOR.MINOR.PATCH is a decision this script must not make
        # on its own — CI's marketplace check fails on it first anyway.
        print(f"{sys.argv[1]}: no MAJOR.MINOR.PATCH version to bump", file=sys.stderr)
        return 1

    major, minor, patch = int(match.group(2)), int(match.group(3)), int(match.group(4))
    new = f"{major}.{minor}.{patch + 1}"
    path.write_text(text[: match.start()] + f'{match.group(1)}{new}{match.group(5)}' + text[match.end():])
    print(f"{sys.argv[1]}: {major}.{minor}.{patch} → {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
