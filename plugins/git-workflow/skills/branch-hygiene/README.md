# branch-hygiene

Cleans up after a merge to `develop` or `main`: retargets any stacked PRs
*before* the parent merges, rebases the open PRs the merge left `CONFLICTING`,
prunes the worktrees and branches the merge orphaned, and closes the issues
whose `Closes #N` keywords silently did nothing because the PR's base was not
the default branch. The failure it prevents is quiet accumulation: stale
branches, stranded children, issues that stay open forever.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

Say any of these; the skill fires on the intent, not on a command:

- "PR 12 merged, clean up"
- "rebase the open PRs"
- "deal with the conflicting PRs"
- "manage the open PRs"

It also fires proactively **before** merging a PR that another open PR is based
on; that is the moment a stack is lost, because merging the parent does not
retarget the child, and deleting the parent's branch *closes* the child.

It deliberately leaves `BLOCKED` and `UNSTABLE` PRs alone: those mean a red
check or a missing review, which a rebase does not fix and a force-push only
reruns.

## Example

A repo squashes PR #2 into `develop`. PRs #3 and #4 were branched from that
work and now show `CONFLICTING`. The skill:

1. Fetches, lists the open PRs, and picks out the two that are `CONFLICTING`.
2. For each, checks how the parent landed (`git merge-base --is-ancestor`
   answers it, the API cannot) and picks the rebase form: a plain
   `git rebase origin/develop` after a merge commit (git auto-skips the
   duplicate patches), or `git rebase --onto` from the parent's old tip after
   a squash (a plain rebase would conflict on every hunk).
3. Inspects the surviving commits, runs the project's test command, then
   `git push --force-with-lease`.
4. Prunes worktrees whose branch is gone and local branches whose PR state is
   `MERGED`, asking the PR, not `git branch --merged`, which cannot see a
   squash-merge at all. Measured 2026-09-02 on one repo: 47 stale branches,
   every one with a MERGED PR, and `--merged` listed almost none of them.
5. Reads the merged PR's body for closing keywords, confirms GitHub fired none
   (`closingIssuesReferences` comes back empty on a develop-based PR), and
   closes each issue by hand citing the merge commit.

The report is one line per PR:

```
PR #3: rebased onto develop, dropped 5 duplicate commits, CLEAN
PR #4: rebased onto develop, dropped 2 duplicate commits, CLEAN
PR #5: was already CLEAN, no action
```

It stops and asks rather than pushing when a rebase empties a branch (the work
is already on the base; the PR should close, not force-push a zero diff), when
a real conflict appears, or when tests fail after the rebase.

## Related

- `rewrite-pr-history`: deliberate history surgery on one PR (drop, reorder,
  split); this skill hands the mechanical post-merge cleanup shape to it and
  takes the rest.
- `pr-comment-loop`: after the rebased PRs re-run their checks, close the loop
  on review comments.
- `worktree-bootstrap`: setting up the temp worktrees this skill creates, when
  they need env files to run tests.
