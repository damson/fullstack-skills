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


## A known-good watcher

Hand-rolling the loop is where the three lies creep in, and one session
rewrote it six times. This shape survived every PR of that session. Fill the
three values from steps 1 and 2, then paste the rest unchanged:

```bash
repo=owner/name                               # fill these three in
pr=123
expected=$(printf '%s\n' validate codecov/patch codecov/project | sort)

sha=$(gh pr view "$pr" --repo "$repo" --json headRefOid --jq .headRefOid)

prev=""; seen=0
for i in $(seq 1 120); do                     # 120 x 30s, a one-hour ceiling
  runs=$(gh api "repos/$repo/commits/$sha/check-runs" \
           --jq '.check_runs[] | {name, status, conclusion}' 2>/dev/null)
  # a review bot or third-party gate posts a legacy commit status, which the
  # check-runs endpoint does not return at all
  stat=$(gh api "repos/$repo/commits/$sha/status" \
           --jq '.statuses[] | {name: .context, conclusion: .state,
                 status: (if .state == "pending" then "queued" else "completed" end)}' 2>/dev/null)
  s=$(printf '%s\n%s\n' "$runs" "$stat" | jq -s '.')
  [ "$(jq -r length <<<"$s")" -gt 0 ] && seen=1
  cur=$(jq -r '.[] | select(.status=="completed") | "\(.name): \(.conclusion)"' <<<"$s" | sort)
  comm -13 <(echo "$prev") <(echo "$cur")     # emit only what newly completed
  prev=$cur
  ready=$(jq -r '.[] | select(.status=="completed") | .name' <<<"$s" | sort -u)
  [ -n "$(comm -23 <(echo "$expected") <(echo "$ready"))" ] || {
    now=$(gh pr view "$pr" --repo "$repo" --json headRefOid --jq .headRefOid)
    [ "$now" = "$sha" ] || { echo "HEAD MOVED $sha -> $now"; sha=$now; prev=""; seen=0; continue; }
    red=$(comm -12 <(echo "$expected") <(jq -r \
      '.[] | select(.status=="completed" and .conclusion!="success") | .name' <<<"$s" | sort -u))
    [ -z "$red" ] && echo "ALL GREEN" || echo "RED: $(echo "$red" | tr '\n' ' ')"
    break; }
  [ "$seen" = 0 ] && [ "$i" -ge 10 ] && { echo "NO RUN for $sha"; break; }
  sleep 30
done
```

Five things in it are load-bearing. It reads **both** surfaces: GitHub Actions
publishes check runs, while review bots and older third-party gates publish
commit statuses, and neither endpoint returns the other's rows, so a watcher on
one of them waits out its whole ceiling for a gate that already passed on the
other. Statuses also carry their own vocabulary, `error` and `failure` where a
check run says `failure`, and both are terminal without being a pass. So the
loop **ends on a verdict, never on the word done**: settled is not passed is
the third lie above, and a bare `DONE` beside a red `validate` is how a session
commits it. The terminal condition is over the **names** step 2 expects, never
over a count: a check nobody expected can make
the count while the one that would have failed the PR never registered, and a
required check behind a path filter registers never. The loop is **bounded** —
an unreachable API or a trigger that will not fire is a report, not a longer
wait, so the counted `for` gives it a ceiling and the `seen` flag turns five
quiet minutes into the diagnostic *When to STOP* asks for. And `expected` is
built with `printf`, because an unquoted `$list` does not word-split in zsh.
Finally the pin is **re-checked at the moment of the verdict, not only at the
start**: a push during the wait makes every conclusion collected so far an
answer about a commit nobody is asking about, so the loop re-pins and keeps
going rather than reporting it.

After a rerun, the newest attempt is already the one you get: the check-runs
endpoint filters to `latest` by default and returns one entry per name, so an old
failure beside a green rerun is not something the loop has to reason about.
Only `?filter=all` returns every attempt, and only then do you need to pick:

```bash
gh api "repos/$repo/commits/$sha/check-runs?filter=all" --jq \
  '[.check_runs[] | select(.status=="completed")] | group_by(.name)
   | map(max_by(.started_at)) | .[] | .name + " :: " + .conclusion'
```

## When to STOP

- **No run registers for the pinned SHA within ~5 minutes.** That is a trigger
  or config problem (path filters, workflow on the wrong branch, Actions
  disabled) — report it; more waiting cannot fix it.
- **Runs keep getting CANCELLED** — a concurrency group is thrashing;
  investigate the group key instead of re-watching.
- **The verdict gates an irreversible action the user did not delegate** —
  green checks authorise reporting, not merging; the merge decision stays
  wherever it lived before.
