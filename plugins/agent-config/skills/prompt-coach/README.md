# prompt-coach

Scores your prompts on the 4Ds (Delegation, Description, Discernment,
Diligence), names the weakest dimension, and proposes one rewrite. The goal is
to make you a more efficient operator over time, not to lecture: one diagnosis,
one denser rewrite, stop.

Read [SKILL.md](SKILL.md) for the procedure and the 1–5 anchors per dimension.

**It never fires unsolicited.** Prompt critique without consent is unwelcome;
you have to ask for it.

## Using it

- "rate my prompt" / "score my last prompt"
- "how am I prompting?" / "give me prompt feedback"
- "4Ds analysis" / "prompt retrospective"
- an end-of-session review of your work-with-Claude habits

Two modes: **Mode A** scores a single prompt you paste or point at. **Mode B**
samples up to 8 prompts evenly spaced across the session, averages per
dimension, and picks one case study.

It declines to score someone else's prompts, defers mid-incident, and pushes
back if you ask for the same evaluation twice within the hour.

## Example

Mode A on the prompt *"Manage the open PRs"*:

```
## Prompt evaluation

> Manage the open PRs

| D | Score | Why |
|---|---|---|
| Delegation | 4/5 | trusts the assistant to pick the mechanics |
| Description | 2/5 | no scope, no expected output, no stop-condition |
| Discernment | N/A — not applicable in this turn |
| Diligence | N/A |

**Weakest dimension**: Description — the assistant cannot tell which PRs,
what "managed" means, or when to stop.

**Rewrite**:
> Rebase PRs #3 and #4 onto develop, force-push, and report one line each.
```

A rewrite never inflates the word count by more than ~30%: the goal is
denser, not longer. Dimensions that cannot logically apply (a first-turn
prompt cannot show Discernment) are marked N/A and excluded from averages.

## Related

- `skill-opportunity-finder`: when Mode B finds a repeated pattern, the full
  skill proposal is deferred to it; prompt-coach only names the candidate.
- `session-retro`: orchestrates prompt-coach Mode B as one axis of a wider
  end-of-session report.
