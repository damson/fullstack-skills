# session-retro

Orchestrates three lenses into one end-of-session report: how you prompted
(`prompt-coach`, Mode B), which repeated patterns deserve to become skills
(`skill-opportunity-finder`), and whether the project's CLAUDE.md still
reflects what shipped (`claude-md-management:claude-md-improver`, if
installed). It is a signal producer only — it applies nothing, and every
section ends with a handoff so you choose what to act on.

Read [SKILL.md](SKILL.md) for the procedure and the exact report shape.

**It never fires unsolicited.** A retrospective is evaluative feedback on your
prompting; it waits to be asked.

## Using it

- "session retro" / "end of session retrospective"
- "wrap up the session"
- "what did we learn this session?"

It stops early when the session has fewer than ~15 substantive turns (too thin
to score), defers mid-incident or mid-deploy, and asks before re-running a
sub-skill you already invoked this session.

## Example

The stitched report, abbreviated:

```markdown
# 🪞 Session retrospective

_Sampled 8 prompts across 31 substantive turns since 10:04._

## 1. Prompting — 4Ds (via `prompt-coach`)
<4Ds table, weakest dimension, one case study with rewrite>

## 2. Skill opportunities (via `skill-opportunity-finder`)
<candidates in priority order, each with a past trigger>

## 3. CLAUDE.md currency (via `claude-md-improver`)
(skipped — `claude-md-improver` not installed)

## 🎯 Suggested next actions
- **Prompting**: state a stop-condition in multi-PR asks
- **New skill**: `refresh-stale-baselines` — plugins/…/skills/
- **CLAUDE.md**: (none — axis skipped)

Want me to drill into any of these? Apply the CLAUDE.md additions?
```

Sub-skill output is preserved verbatim — the sub-skills are the source of
truth on their own axis; only the "Suggested next actions" synthesis is the
orchestrator's. A skipped sub-skill is declared up front, never buried.

## Related

- `prompt-coach` — axis 1, invoked in Mode B; ships in this plugin.
- `skill-opportunity-finder` — axis 2; ships in this plugin.
- `claude-md-management:claude-md-improver` — axis 3; a separate third-party
  plugin. When it is not installed the axis degrades to a recorded skip — the
  retro never fails over it and never inlines an imitation.
- `save-before-compact` — the applying sibling: run it when you want the
  learnings written, not just reported.
