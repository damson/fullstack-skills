# skill-opportunity-finder

Watches a session for the same shape of work happening three or more times
(repeated corrections, repeated multi-step operations, repeated discovery,
repeated meta-instructions) and proposes the skills that would have caught
them. The failure it prevents: paying the same instruction tax every session
because nobody noticed it had become a pattern.

Read [SKILL.md](SKILL.md) for the four pattern classes and the clustering
rules.

## Using it

It fires on its own when it notices you repeating an instruction, question,
correction or manual operation three or more times. You can also ask:

- "what should be a skill?"
- "what am I doing manually?"
- "where am I repeating myself?"

It stays quiet during the first ~5 turns of a session (patterns need history
to be observable) and reports "no patterns yet" rather than manufacturing a
candidate. A declined proposal is not re-proposed in the same session, and a
candidate that duplicates an existing skill is pointed at, not recreated.

## Example

After the third "reply to the review comments and push" of a session:

```markdown
## Skill opportunities found in this session

### 1. review-reply-loop — the same fetch → classify → reply → push ran three times

**Past trigger (turn 14)**: "check the comments on PR 7 and address them"

**Draft SKILL.md**:
---
name: review-reply-loop
description: <auto-trigger conditions>
---
# Review reply loop
<2-4 sentences explaining purpose>
## Procedure
1. ...
## When to STOP
- ...
```

Two events count as the same shape only when artefact class, verb family and
trigger boundary all match (three instances suffice); two of three matching
raises the bar to four instances. Each candidate comes with one concrete past
moment where it would have helped.

The skill also encodes the boundary that keeps it honest: "ALWAYS do X" is a
CLAUDE.md note; "WHEN trigger THEN procedure" is a skill. It never proposes
skills that fire on every turn, one-off operations, or anything that pre-empts
your judgement on irreversible decisions.

## Related

- `prompt-coach`: names a skill candidate from its Mode B pattern analysis
  and defers the full proposal here.
- `session-retro`: invokes this skill as one axis of the end-of-session
  report.
- `save-before-compact`: invokes this skill before compaction, and creates
  the approved candidates while the session context still exists.
