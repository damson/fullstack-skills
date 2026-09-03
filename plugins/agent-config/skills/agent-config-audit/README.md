# agent-config-audit

Audits the AI instruction files that are actually loaded for the current
project (global and project `CLAUDE.md`, `AGENTS.md`, preference files) for
contradictions, duplication, bloat, and personal rules that leaked into team
files. The failure it prevents: a config stack that grew by accretion, where two
files disagree about the same convention and the agent silently obeys whichever
it read last.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

Ask in any of these shapes:

- "audit my agent config"
- "which instruction files are actually active here?"
- "check CLAUDE.md and AGENTS.md for contradictions"
- after restructuring how your config is organised, or when onboarding to a
  new project

Three flags narrow or extend a run: `--team` (only the team `AGENTS.md`),
`--personal` (only personal files), `--fix` (after reporting, propose edits and
apply each **on approval**; it never batch-applies without asking).

It reports first, always. Without `--fix` nothing is written.

## Example

On a project whose `AGENTS.md` picked up a personal commit-style rule, the
report looks like:

```
## Agent Config Audit

### Active File Stack
| Logical path | Source | Owner |
|---|---|---|
| ~/.claude/CLAUDE.md | `<config-repo>/personal/CLAUDE.md` | personal |
| <project>/AGENTS.md | (plain file, no symlink) | team |

### Findings

🚧 Boundary violation — AGENTS.md: Commits
  Personal rule "no pod prefix" found in team AGENTS.md.
  Recommendation: move to personal CLAUDE.md

⚠️ Duplication — AGENTS.md: Testing duplicates CLAUDE.md: Testing
  Recommendation: keep in AGENTS.md, remove from CLAUDE.md

✅ OK — 23 rules checked, no other issues
```

Symlinked config repos get an extra structural-health check (broken chains,
copies that should be links); plain files in place are a valid setup, not a
finding; that check is skipped when no symlinks exist.

## Related

- `claude-md-pointer-check`, the file-shape half: keeps a CLAUDE.md a pointer
  to its sibling rather than a copy; this skill audits the rules inside the
  whole stack.
- `redundancy-check-before-ship`: the same dedup instinct applied to a single
  diff before it is committed, rather than to the standing stack.
