# agent-config

Writing and auditing agent instruction files: eight skills for keeping a
`CLAUDE.md` stack honest, and for noticing when a session has taught you
something worth writing down.

```bash
claude plugin install agent-config@hard-won-skills --yes
```

Instruction files fail quietly: a rule duplicated into two files drifts until
they contradict each other, a "helpful" addition restates what a sibling
already says, and a long session's hard-won lessons evaporate the moment the
context is compacted. These skills audit the stack, keep every rule in exactly
one home, and catch the learnings before they're gone.

Three of them (`prompt-coach`, `save-before-compact`, `session-retro`) are
consent-gated: they evaluate *you*, so they never fire unsolicited.

## The skills

| Skill | What it does |
|---|---|
| [`agent-config-audit`](skills/agent-config-audit/README.md) | Resolve which instruction files actually load, then audit the stack for contradictions, duplication, bloat and boundary violations |
| [`claude-md-pointer-check`](skills/claude-md-pointer-check/README.md) | Before writing a CLAUDE.md: if a sibling already covers it, write a pointer plus the Claude-only delta, not a copy |
| [`redundancy-check-before-ship`](skills/redundancy-check-before-ship/README.md) | Before committing prose rules: grep each added rule against what the reader already has loaded, ship only the net-new |
| [`skill-opportunity-finder`](skills/skill-opportunity-finder/README.md) | Spot the instruction you've repeated three times and propose the skill it should become |
| [`validate-skill-against-real-project`](skills/validate-skill-against-real-project/README.md) | Run a portable skill's own commands against a real project: reading it is not testing it |
| [`prompt-coach`](skills/prompt-coach/README.md) | Score your prompts on the 4Ds and propose one denser rewrite (on request only) |
| [`save-before-compact`](skills/save-before-compact/README.md) | Before compacting a long session: route each learning to its right home, per-item approved, then write a resume brief |
| [`session-retro`](skills/session-retro/README.md) | One end-of-session report from three lenses (prompting, skill opportunities, CLAUDE.md currency), applying nothing |

Each skill's README carries its triggers and a worked example; the `SKILL.md`
beside it is the procedure the agent follows.
