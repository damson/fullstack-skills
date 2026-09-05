# watch-what-the-merge-triggered

Watches the `on: push` run that a merge starts, pinned to the merge commit, and
separates "nothing ran" from "nothing was supposed to run". A pull request's
checks run on a merge *preview* with pull-request-scoped secrets. The merge
produces a different commit, and workflows run against it holding credentials a
pull request was deliberately denied, so that run is the first and only exercise
of merge-time credentials and nothing before it could have been.

Read [SKILL.md](SKILL.md) for the procedure. This file is what a run looks like
and when to reach for it.

## Using it

Reach for it the moment a merge lands on a branch something watches:

- "merged", "it landed", "that's in now", where the base has deploy, migrate,
  publish or notify workflows
- the merged PR touched a workflow file, or a path some workflow filters on
- a brand-new deploy or migrate workflow is merged for the first time

It does **not** fire for a merge into a branch nothing watches, and it does not
own the PR's own checks: `await-pr-checks`, in this plugin, does. Confirming
that the merged diff contains what was claimed is a question about content, not
about runs, and is somebody else's job.

## Example

A migrate workflow merges into `main`.

1. **Get the merge commit and check its shape.**
   `mc=$(gh pr view <n> --json mergeCommit --jq .mergeCommit.oid)`, then assert
   it is 40 hex characters. An unmerged PR, a wrong number, or a merge queue
   still holding the merge all yield empty or the literal `null`, which matches
   nothing for the whole polling budget and is then reported as the legitimate
   "no run" outcome. Without the check, a typo produces a confident all-clear.
2. **Work out what should have started, before looking at what did.** Read the
   triggers on the *base* branch, since that is the version that fires, and list
   the merge's files with `git show --name-only --format= --first-parent "$mc"`.
   `--first-parent` is load-bearing: a merge commit's default diff is against
   all its parents at once, so plain `git show --name-only` prints nothing for
   one, and every path-filtered workflow then reads as untriggered. A squashing
   repo never sees this, which is how it survives being copied between repos.
3. **Watch each to a terminal state, filtered by SHA.** Bound the wait by the
   workflow's own largest `timeout-minutes` plus one, and poll
   `gh run list --json databaseId,headSha,status,conclusion` selecting on
   `$mc`. A run for the branch tip is the PR's run; a run for "the latest push
   to base" may be somebody else's merge a minute later.
4. **Read the jobs, not the run.** A green run whose reporting job was
   `skipped` has proved nothing about that job. An `if: failure()` notifier does
   not run on a healthy merge, so it stays unproven and the report says so.
5. **Name what the run proved and what it did not**, one line each, in the reply
   that reports the merge. The secret exists and authenticates; the filters
   match reality. Not: anything in a skipped job, or any second environment
   whose secret this run never read.

A run with zero jobs is not a code failure. The reason lives only in the run's
annotations, and a merge also kills the PR's in-flight runs, which are recorded
as failures with zero jobs at the merge time.

## Why it is shaped like this

- **"Nothing ran" and "nothing was supposed to run" look identical afterwards
  and mean opposite things.** Working out the expected list first is the only
  thing that separates them, which is why step 2 comes before step 3.
- **Merge-time credentials get exactly one rehearsal, and this is it.** The
  secret that a pull request could not read is read here for the first time,
  against the real target.
- **Three failure causes need separating before anything is fixed**: a refused
  run (billing, approval, permissions, visible only in annotations),
  configuration that exists only post-merge, and a real defect. Only the last is
  a code fix, and the middle one belongs in a follow-up PR rather than a push to
  the branch just merged into.

## Related

- `await-pr-checks`, the other half of the pair: it owns the pull request's own
  checks, this owns the run the merge starts.
- `close-the-release-cycle`, which has its own reason to care that a merge
  performed by a CI token raises no push event, so a workflow gated on one never
  runs.
