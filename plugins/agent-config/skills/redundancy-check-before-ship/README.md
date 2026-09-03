# redundancy-check-before-ship

Runs before committing an addition to any prose-rule file (CLAUDE.md,
AGENTS.md, a docs/ page, a README, a PR template) and greps each added rule
against the docs a reader already has loaded. The failure it prevents: prose
rules duplicating silently, because the author remembers writing the sentence
but not that the repo already states it somewhere else.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

It auto-triggers after writing a prose-rule addition and before `git commit`.
You can also ask directly:

- "is this addition really necessary?"
- "this file is too big" / "this doc has duplicates"

It skips code, tests, config values, pure deletions, rewording that adds no
rule, and new files with no sibling docs. The CLAUDE.md-vs-sibling
file-structure case is handed to `claude-md-pointer-check`; this skill covers
rule-level dedup in any prose file.

## Example

A diff adds three bullets to a repo's CONTRIBUTING.md. The skill splits them
into individual claims (a bullet saying "start from the template, never
free-hand, and tick nothing you did not verify" is three rules), greps each
subject across the sibling docs, and reports before the commit:

```
Rules added: 5
Already stated elsewhere: 3
  - "start from the PR template"      → .github/PULL_REQUEST_TEMPLATE.md (keep there, drop here)
  - "tick only verified boxes"        → PR template review section (drop)
  - "one focused change per commit"   → CLAUDE.md Git section (drop, link instead)
Net new: 2
File delta after pruning: +4 lines instead of +14
```

Two judgement calls it encodes: a rule may legitimately live in an always-
loaded entry-point file *and* a reference doc (different distances from use),
and relocation is only worth it when the destination already has a section on
the subject; otherwise drop the block. If a file claims to be portable, the
added rule is also checked for hardcoded repo names, tools and paths, the most
common portability leak.

## Related

- `claude-md-pointer-check`: the file-shape rewrite for CLAUDE.md
  specifically; this skill is per-rule and works on any prose file.
- `agent-config-audit`: finds the same duplication after it shipped; this
  skill is the gate that keeps it from shipping.
