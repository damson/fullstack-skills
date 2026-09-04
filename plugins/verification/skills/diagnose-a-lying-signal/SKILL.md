---
name: diagnose-a-lying-signal
description: >
  Use when a status surface and reality disagree: a green check for work that
  cannot have happened, a badge reading "unknown" or an implausible number, a
  run that failed with nothing in it, a command that "found nothing" it should
  have found. Fires on "the check is green but...", "the badge still says
  unknown", "why did that fail with nothing in the log", "it says it passed but
  nothing ran", "that number cannot be right". Do NOT fire for an honest failure
  with a real error in a real log:
  that is debugging, and the log is already telling the truth.
---

# Diagnose a signal that lies

A green check, a badge and an exit code are all summaries, and a summary is
produced by something that can be wrong about it. When the summary disagrees
with what you know, the first move is not to debug the underlying work: it is
to find the authoritative record and read that instead. Every hour lost to this
class of problem is spent fixing something that was never broken.

## Procedure

1. **State the disagreement in one sentence**, in the form "X reports Y, but Z
   cannot be true at the same time." If you cannot, this skill does not apply;
   see *When to STOP*.

2. **Name the surface and its authoritative source.** They are never the same
   object. Common pairs:

   | Surface | What actually holds the answer |
   |---|---|
   | A check on a PR | the run's jobs and steps, and their conclusions |
   | A step reported green | the step's own log, plus whether it was allowed to fail |
   | A published badge | the service's API record for that commit and branch |
   | An exit status | the status of the command you meant, not of a pipeline |
   | "No matches" | whether the command ran at all |

3. **Read the source, not a rendering of it.** Fetch the record and quote what
   it says. Three renderings that routinely mislead — `<o>/<r>` is the owner and
   repository, `<id>` the run id the surface itself names:

   ```bash
   # A run that failed with no jobs is a startup failure, not your code
   gh api repos/<o>/<r>/actions/runs/<id>/jobs --jq .total_count

   # A step's own conclusion, which a "do not fail the build" setting hides from
   # the job's rolled-up status; read it before reading the log for a reason why
   gh api repos/<o>/<r>/actions/runs/<id>/jobs \
     --jq '.jobs[].steps[] | select(.conclusion != "success") | {name, conclusion}'

   # An image is not data: parse the text node, never grep the markup
   curl -s "<badge-url>" | tr '>' '\n' | grep -E '^(unknown|[0-9]+%)'
   ```

   The commands are one host's; the move is not. Anywhere else, find the endpoint
   that returns the record rather than the page that renders it, and where the
   host publishes none, report that the surface could not be checked instead of
   trusting it.

4. **Suspect the reporter before the work**, in this order, because this is the
   order of frequency: the surface is scoped to something else (a different
   branch, a different commit, a stale cache); the failure was swallowed by a
   "do not fail the build" setting; the summary belongs to a different command
   than the one you care about (a pipeline reports its **last** element); the
   record was never produced at all.

5. **Confirm the true state from a second, independent angle** before acting on
   it. A single API read can be as stale as the badge was.

6. **Fix the reporter and the work separately, and say which you fixed.**
   "The badge was pointed at a branch nothing uploads to" and "coverage is low"
   are different findings with different owners, and conflating them is how a
   correct pipeline gets rewritten to chase a display bug.

## Sharp edges

- **Absence of a record is not the same as a failed record.** "Never uploaded",
  "uploaded and rejected", and "uploaded and still processing" look identical
  from the surface, need different fixes, and only the authoritative source
  tells them apart.
- **The reporter can be right and still be measuring something else.** A badge
  scoped to one branch, a check attached to an older commit, and a cached image
  are all accurate answers to a question you did not ask.

## When to STOP

- **You cannot state the disagreement as a contradiction.** There is no lying
  signal, only an expectation. Go look at the work instead.
- **The log holds a real error about real work.** Nothing is lying; debug it.
- **The authoritative source agrees with the surface.** Then the surface is
  right and the expectation was wrong; say so plainly rather than hunting for a
  reporter bug that is not there.
- **The fix belongs to a service's account state** (a repository never
  activated, an app never granted access). Report it with the evidence; it is
  not fixable from the repository, and guessing at repo-side fixes for it burns
  time and leaves debris.
- **Two independent reads disagree.** Before blaming a cache, check they asked
  the same question — same commit, same branch, same scope — and that both were
  taken after the last write. Once they were, it is a cache or a lagging
  replica: wait or bypass it explicitly, and conclude nothing until they agree.
