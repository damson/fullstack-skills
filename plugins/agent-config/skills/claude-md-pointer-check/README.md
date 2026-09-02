# claude-md-pointer-check

Fires before a CLAUDE.md is created or substantially edited, and checks whether
a sibling `AGENTS.md` or `README.md` already covers the planned content. If it
does, the CLAUDE.md becomes a one-line pointer plus only the Claude-specific
delta. The failure it prevents: the byte-for-byte duplicate that costs
conciseness the day it is written and drifts into contradiction afterwards.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

The skill fires on the *act*, not on a phrase — any time a CLAUDE.md is about
to be written or reshaped:

- "add a CLAUDE.md to this repo"
- "update the project's CLAUDE.md with the build commands"
- creating a CLAUDE.md as part of scaffolding a new project

It steps aside for typo- and line-level fixes, when there is no sibling to
point at (greenfield — write normally), when the user explicitly wants a
standalone file, when the existing CLAUDE.md is already a pointer, when the
duplication is deliberate — and, resolved before any comparison, when the
sibling `AGENTS.md` is a symlink to the very CLAUDE.md being edited, which
makes CLAUDE.md the canonical copy rather than the duplicate.

## Example

A repo has an `AGENTS.md` with the team's conventions, and the planned
CLAUDE.md would restate most of them plus two Claude-only rules. The skill
applies the deletion test per section — would dropping it lose any fact or
command a sibling does not already state? — finds more than half fail it,
and rewrites the whole file as:

```markdown
# CLAUDE.md — acme-api

Read [README.md](README.md) first — it covers commands, architecture, and
git flow. The directives below are Claude-only and don't belong in README.

## Claude-only directives

- `.claude/settings.json` cannot be auto-written from this repo
- When adding an entry, edit the registry file only — never touch the
  scripts that read it
```

While there, it also lints the sibling for phrases that read as rules but
cannot be acted on ("leave it better than you found it", "stay scoped") and
proposes concrete replacements — asking before touching the sibling, which may
be team-owned.

## Related

- `redundancy-check-before-ship` — rule-level dedup across any prose-rule
  file; this skill owns the CLAUDE.md-vs-sibling file-structure case
  specifically.
- `agent-config-audit` — audits the whole loaded config stack after the fact;
  this skill prevents one class of its findings from being written.
