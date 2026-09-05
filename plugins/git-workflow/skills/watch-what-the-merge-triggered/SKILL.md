---
name: watch-what-the-merge-triggered
description: >
  Use immediately after merging into a branch that workflows watch — an
  integration branch, a release branch, anything with `on: push`. Fires on
  "merged", "it landed", "that's in now" when the base has deploy, migrate,
  publish or notify workflows, and whenever a merged PR touched a workflow file
  or a path some workflow filters on. Owns the run the MERGE starts: which
  workflows it triggers, watching them to a terminal state pinned to the merge
  commit, and treating that run as the first and only exercise of merge-time
  credentials. Do NOT fire for a merge into a branch nothing watches, for the
  PR's own checks (await-pr-checks owns those), or to confirm that the merged
  diff contains what was claimed, which is a question about content rather than
  about runs.
---

# Watch what the merge triggered

A pull request's checks run on a merge *preview*, with pull-request-scoped
secrets. The merge produces a different commit, and `on: push` workflows run
against it holding credentials a pull request was deliberately denied — so the
first run after a merge is not a repeat of the PR's checks but the first
execution of a configuration nothing could have tested.

The failure it catches is specific: **code that only runs after a merge, and
tooling that only runs after a failure.** Both are invisible until they are the
only thing left working.

## Procedure

### 1. Get the merge commit, and hold it

```bash
mc=$(gh pr view <n> --json mergeCommit --jq .mergeCommit.oid)
base=$(gh pr view <n> --json baseRefName --jq .baseRefName)
case "$mc" in [0-9a-f]*[0-9a-f]) [ ${#mc} -eq 40 ] || exit 1;; *) exit 1;; esac
```

**Check the shape before using it.** An unmerged pull request, a wrong number,
or a merge queue still holding the merge all give an empty string or the literal
`null`, and every step below interpolates `$mc` into a filter that then matches
nothing. Step 3 reads "no run for `$mc`" as a legitimate answer, so without this
guard a typo produces a confident all-clear.

Every read below is pinned to `$mc`. A run for the branch tip is the PR's run,
and a run for "the latest push to base" may be somebody else's merge a minute
later — which is not a hypothetical on a repo with more than one session
working.

### 2. Work out what SHOULD have started, before looking at what did

Read the triggers **on the base branch**, because that is the version that
fires, and compare them against what the merge changed:

```bash
git fetch --prune
git show --name-only --format= --first-parent "$mc"     # what the merge changed

# The candidates: every workflow on the base branch with a push trigger.
for w in $(git ls-tree --name-only "origin/$base" .github/workflows/); do
  git show "origin/$base:$w" | grep -qE '^on:|push:' && echo "$w"
done
git show "origin/$base:.github/workflows/<file>" | sed -n '1,40p'   # one on: block
```

Two things decide it: the `branches:` filter must contain `$base`, and any
`paths:`/`paths-ignore:` filter must match — or fail to exclude — one of the
changed files. Read both lists against that file list; a workflow with
no path filter matches every push to that branch.

**`--first-parent` is load-bearing where the base takes merge commits.** A merge
commit's default diff is against *all* its parents at once, so `git show
--name-only` prints nothing for one — not an error, an empty list, which reads
as "no path filter matched". A squashing repo never sees it, which is how it
survives being copied between repos.

**A workflow listed in its own `paths:` filter fires on the merge that adds
it.** That is the common surprise, and it is the moment a brand-new deploy or
migrate workflow runs for the very first time — against production-adjacent
credentials, on a commit nobody has tested it on.

Knowing the expected list first is what separates *"nothing ran"* from
*"nothing was supposed to run"*. They look identical afterwards and mean
opposite things.

### 3. Watch each to a terminal state, filtered by SHA

Set the bound first — the workflow's own `timeout-minutes` plus one is the only
limit the run cannot exceed:

```bash
# The LARGEST timeout in the file, not the first: a multi-job workflow's first
# `timeout-minutes` may belong to a job you are not watching, and a bound that
# is too short reports "no verdict" for a run still working.
mins=$(git show "origin/$base:.github/workflows/<file>" | grep -oE 'timeout-minutes: *[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)
tries=$(( ( ${mins:-15} + 1 ) * 3 ))            # 20s per try

for _ in $(seq 1 "$tries"); do
  r=$(gh run list --workflow <file> --limit 5 \
        --json databaseId,headSha,status,conclusion \
        --jq "[.[] | select(.headSha==\"$mc\")] | .[0] // empty")
  [ -n "$r" ] || { sleep 20; continue; }          # not registered yet
  echo "$r"
  case "$r" in *'"status":"completed"'*) break;; esac
  sleep 20
done
```

```bash
run_id=$(printf '%s' "$r" | jq -r .databaseId)   # what step 4 reads
```

Judge by `status` then `conclusion`, per the checks-watching discipline
(`await-pr-checks`). Two answers are not failures and must not be read as any:

- **no run for `$mc` after ~5 minutes**, when step 2 said none was expected —
  correct, say so;
- **a run with zero jobs** — the trigger or the account refused it, not the
  code. The reason lives only in the run's annotations, not in any job log:
  `gh api "repos/{owner}/{repo}/check-runs/$run_id/annotations"`, or
  `gh run view "$run_id" | grep -A2 ANNOTATIONS`.

### 4. Read the jobs, not the run

```bash
gh run view "$run_id" --json jobs --jq '.jobs[] | "\(.conclusion)\t\(.name)"'
```

A green run whose reporting job was `skipped` has proved nothing about that
job. This is where the value is: an `if: failure()` notifier does not run on a
healthy merge, so **it is still unproven** and the report must say so rather
than implying the workflow is exercised.

If a job did run, read what it printed rather than its colour. A job that
"succeeded" having found nothing to do is a different fact from one that did
the work.

### 5. Name what the run proved, and what it did not

**Where the claims go:** into the reply that reports the merge, one line each — this
is the report, not a note to yourself. Where a pull request is still open on
the same subject, the same lines go in its sticky comment so the record
outlives the session. Never a new file.

State each claim with the evidence beside it:

- the environment secret exists, is scoped to this branch, and authenticates;
- the identity checks passed against the real target;
- the workflow's own `paths` and `branches` filters match reality.

And the claims it does **not** support: anything in a skipped job, anything on
a path the merge did not touch, and anything about a second environment whose
secret this run never read.

### 6. On failure, separate the three causes before fixing anything

| Symptom | Cause | Where the evidence is |
|---|---|---|
| Job fails in seconds, no useful log | The run was refused (billing, approval, permissions) | run annotations |
| Job runs, fails on a missing secret or a name | Configuration that only exists post-merge | the step's own output |
| Job runs, fails on the code | A real defect the PR's checks could not see | the log, as usual |

Only the third is a code fix. The first is not yours, and the second belongs in
a follow-up PR — never a push to the branch you just merged into.

## Sharp edges

- **`git merge-base --is-ancestor <branch-tip>` is not a merge test** where
  merges are squashed. Ask about `$mc`, which is on the base by construction.
- **A merge kills the PR's in-flight runs.** A run recorded as failed with zero
  jobs, updated at the merge time, is that — not a new failure to chase.

## When to STOP

- **The base is watched by nothing.** Say so in one line and stop; there is no
  run to wait for.
- **A run fails for a reason outside the repository** — billing, a disabled
  workflow, a queue. Report the annotation verbatim and hand back; retrying
  cannot fix an account.
- **The fix belongs on the branch you just merged into.** Open a pull request.
  A post-merge failure is not a licence to push to an integration branch.
- **The failing workflow is somebody else's**, or touches a system this session
  was not asked to operate. Report which run and which job, and stop.
