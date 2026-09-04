---
name: await-pr-checks
description: >
  Use when waiting on a pull request's CI before acting — "merge when green",
  "wait for the checks", "watch the run", "is CI green?" — and before REPORTING
  a PR's check state after any push, including one this session made. Also fire
  when a wait loop is about to be written with `gh pr view`/`gh run list` in
  it. Goal — a terminal verdict per named check, never a report that mistook
  silence, an empty field, or the previous run for an answer. Do NOT fire to
  merge on the result (green authorises reporting, not merging: that is
  `merge-on-go-ahead`), to diagnose a check that has already reported red (read
  its log), or for a run with no pull request behind it.
---

# Await PR checks

Three ways a hand-rolled wait loop lies, each observed in the wild in one
session:

1. **An empty conclusion reads as done.** `.conclusion // .status` renders a
   queued check as an empty string; a filter that greps for the *absence* of
   `PENDING|IN_PROGRESS` then passes on nothing at all. The loop exits, the
   check was failing.
2. **The watcher races the push.** Started right after `git push`, it reads the
   rollup before the new run registers — and faithfully reports the *previous*
   run's terminal state as the verdict.
3. **"Settled" is not "passed."** A loop that exits when nothing is pending has
   no idea whether it exited green or red, and the report inherits the
   ambiguity.

## Procedure

1. **Pin the head SHA first.**
   `sha=$(gh pr view N --json headRefOid --jq .headRefOid)` — and if you just
   pushed, confirm it equals the commit you pushed. Every later read is judged
   against this SHA; never watch "the latest run" unpinned.

2. **Enumerate the checks you expect by name** — from the required-checks
   ruleset, the previous run, or the workflow files *read on the base branch,
   not the PR's*: a PR can rename or delete exactly the check that would have
   failed it. The terminal condition is over this list — a missing check is
   *pending*, not passing.

3. **Poll on these rules** (30s for hosted runners; back off, don't tighten):
   - A run counts only if its `headSha` equals the pinned SHA — and only its
     newest attempt: a rerun keeps the SHA but opens a fresh `run_attempt`, so
     an older attempt's terminal state is not the verdict.
   - A check is terminal only when its `status` is `COMPLETED` — then judge
     the `conclusion`: `SUCCESS` passes; `FAILURE`, `CANCELLED`, `TIMED_OUT`,
     `ACTION_REQUIRED`, `STARTUP_FAILURE` fail; `SKIPPED`, `NEUTRAL`, `STALE`
     are a per-check decision to make explicitly, never by omission. Anything
     not completed — empty, `QUEUED`, `IN_PROGRESS`, `PENDING` — keep waiting.
   - If `headRefOid` moves mid-watch, the answer is void: re-pin and restart.

4. **On any non-success, fetch the cause in the same motion.** Resolve the
   failing check to its workflow run for the pinned SHA, then
   `gh run view <run-id> --log-failed | tail`. A check with no Actions run
   behind it (an external status — a review bot, a third-party gate) keeps its
   evidence at its `details_url`: follow that, or report the logs as
   unavailable — never skip the cause because the id was not obvious.

5. **Report per check, by name** (`Coverage report: SUCCESS, ShellCheck:
   SUCCESS`), never a bare "checks are green". A verdict that names nothing
   cannot be checked against reality later.

## When to STOP

- **No run registers for the pinned SHA within ~5 minutes.** That is a trigger
  or config problem (path filters, workflow on the wrong branch, Actions
  disabled) — report it; more waiting cannot fix it.
- **Runs keep getting CANCELLED** — a concurrency group is thrashing;
  investigate the group key instead of re-watching.
- **The verdict gates an irreversible action the user did not delegate** —
  green checks authorise reporting, not merging; the merge decision stays
  wherever it lived before.
