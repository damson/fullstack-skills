#!/usr/bin/env python3
"""Check the marketplace's manifests and README agree with what is on disk.

The skill *contents* are checked by validate-skills.sh. What this covers is the
wiring around them, which drifts silently: a plugin added to the tree but not to
marketplace.json is invisible to `claude plugin install`, and a README count
that no longer matches reality is the kind of thing nobody notices until someone
trusts it.

Reports every problem before exiting, so one run lists all the work.
Standard library only — it must run on a fresh runner with no pip step.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

problems = []


def problem(msg):
    problems.append(msg)


def plugin_dirs():
    return sorted(p for p in (ROOT / "plugins").iterdir() if p.is_dir())


def skills_of(plugin):
    d = plugin / "skills"
    if not d.is_dir():
        return []
    return sorted(s.name for s in d.iterdir() if s.is_dir() and (s / "SKILL.md").is_file())


def check_manifests():
    """marketplace.json and every plugin.json parse and agree with the tree."""
    path = ROOT / ".claude-plugin" / "marketplace.json"
    try:
        market = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        problem(f"marketplace.json is unreadable: {exc}")
        return {}

    listed = {}
    for entry in market.get("plugins", []):
        name = entry.get("name", "<unnamed>")
        source = entry.get("source", "")
        listed[name] = entry
        # A source that does not resolve installs nothing, with no error until
        # someone tries it.
        if not (ROOT / source.lstrip("./")).is_dir():
            problem(f"marketplace.json: plugin '{name}' source does not exist: {source}")
        if not entry.get("description", "").strip():
            problem(f"marketplace.json: plugin '{name}' has no description")

    on_disk = {p.name for p in plugin_dirs()}
    for missing in sorted(on_disk - set(listed)):
        problem(f"plugins/{missing}/ exists but marketplace.json does not list it")
    for phantom in sorted(set(listed) - on_disk):
        problem(f"marketplace.json lists '{phantom}' but plugins/{phantom}/ does not exist")

    for plugin in plugin_dirs():
        manifest = plugin / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            problem(f"plugins/{plugin.name}/ has no .claude-plugin/plugin.json")
            continue
        try:
            data = json.loads(manifest.read_text())
        except json.JSONDecodeError as exc:
            problem(f"plugins/{plugin.name}/.claude-plugin/plugin.json is invalid: {exc}")
            continue
        if data.get("name") != plugin.name:
            problem(
                f"plugins/{plugin.name}: plugin.json name is "
                f"'{data.get('name')}' — it must match the folder name"
            )
        version = str(data.get("version", ""))
        if not SEMVER.match(version):
            # The release job bumps the patch field; anything else it cannot parse.
            problem(f"plugins/{plugin.name}: version '{version}' is not MAJOR.MINOR.PATCH")

    return listed


def check_readme():
    """The README's counts and skill lists match the tree.

    This is the check that would have caught the 7 → 8 edit being made by hand.
    """
    readme = (ROOT / "README.md").read_text()

    for plugin in plugin_dirs():
        skills = skills_of(plugin)

        row = re.search(
            rf"^\|\s*\*\*{re.escape(plugin.name)}\*\*\s*\|\s*(\d+)\s*\|",
            readme,
            re.MULTILINE,
        )
        if not row:
            problem(f"README.md: no table row for plugin '{plugin.name}'")
        elif int(row.group(1)) != len(skills):
            problem(
                f"README.md: table says {plugin.name} has {row.group(1)} skills, "
                f"the tree has {len(skills)}"
            )

        # Each plugin's section ends with a backtick list of its skills. A skill
        # absent from it is undocumented; a name present but gone from the tree
        # sends readers looking for something that was renamed or removed.
        # Stop at the next heading of ANY level. Anchoring on '### ' alone runs
        # the last plugin's section into the README's trailing prose, where
        # backticked words like `bats` read as skill names.
        section = re.search(
            rf"^### {re.escape(plugin.name)}$(.*?)(?=^#{{1,6}} |\Z)",
            readme,
            re.MULTILINE | re.DOTALL,
        )
        if not section:
            problem(f"README.md: no '### {plugin.name}' section")
            continue
        named = set(re.findall(r"`([a-z0-9-]+)`", section.group(1)))
        for skill in skills:
            if skill not in named:
                problem(f"README.md: '### {plugin.name}' does not mention skill '{skill}'")
        for stale in sorted(named - set(skills)):
            problem(f"README.md: '### {plugin.name}' names '{stale}', which is not in the tree")


def main():
    check_manifests()
    check_readme()

    if problems:
        for p in problems:
            print(f"⚠ {p}", file=sys.stderr)
        print(f"✗ {len(problems)} problem(s) in the marketplace wiring", file=sys.stderr)
        return 1
    total = sum(len(skills_of(p)) for p in plugin_dirs())
    print(f"✔ {len(plugin_dirs())} plugin(s), {total} skill(s) — manifests and README agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
