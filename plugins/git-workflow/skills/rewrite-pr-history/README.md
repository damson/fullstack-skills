# rewrite-pr-history

Deliberate surgery on an open PR's history — dropping a commit, reordering,
splitting, rewording — done so that nothing is lost and nothing shared is
force-pushed. It shows the plan and waits for an explicit "go" before
rewriting, and it never reaches for plain `--force`. The failure it prevents is
the unrecoverable one: work destroyed by a rewrite that seemed routine.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

- "remove the X commit from PR 9"
- "reorder the commits on this branch"
- "drop the last commit"
- "clean up the history before review"

It does **not** fire for the routine post-merge rebase of open PRs (duplicate
commits after a parent landed) — that is mechanical cleanup and belongs to
`branch-hygiene`. This skill is for edits you chose to make.

## Example

"Drop the debug commit in the middle of PR #9." The skill:

1. Reads the PR state and confirms the head branch is not `main`, `master`,
   `develop` or shared, and that no approved review is about to go stale — if
   one is, it asks first, because review comments anchor to commits.
2. Syncs and confirms a clean working tree (a dirty one stops the run — it
   never auto-stashes).
3. Shows the plan — `git log --oneline origin/<base>..HEAD`, the diff stat, and
   the intended command in plain words — then **waits for "go"**.
4. Rewrites with the smallest-blast-radius command; for a mid-branch drop:

   ```bash
   git rebase --onto <base> <commit-to-drop> <branch>
   ```

   Reordering has no terminal to run `git rebase -i` in, so the todo-list edit
   goes through the sequence editor instead:
   `GIT_SEQUENCE_EDITOR=<script> git rebase -i <base>`.
5. Runs the project's test command and the CI linter locally, then pushes with
   `git push --force-with-lease` — which refuses to clobber if the remote moved
   since the last fetch.
6. Verifies on the platform that the commit list matches the plan and the PR is
   `MERGEABLE`.

If `--force-with-lease` is rejected, it stops and surfaces the difference
between expected and actual remote state — switching to plain `--force` is
never the answer.

## Related

- `branch-hygiene` — the mechanical post-merge rebase this skill deliberately
  does not duplicate.
- `pr-comment-loop` — re-check review comments after the rewrite invalidates
  their anchors.
