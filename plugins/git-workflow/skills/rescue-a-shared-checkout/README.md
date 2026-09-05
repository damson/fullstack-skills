# rescue-a-shared-checkout

Separates the uncommitted changes in a shared working tree into the ones already
safe, the ones genuinely at risk, and the ones that are somebody's work in
progress — then lands only the middle group, without committing from the shared
tree. Uncommitted work in a tree with more than one writer is the least safe
state a repository has: nothing records who wrote it, nothing preserves it, and
the next branch cut from that tree carries it by accident.

Read [SKILL.md](SKILL.md) for the procedure. This file is what a run looks like
and when to reach for it.

## Using it

Reach for it when the dirt in a tree is not yours:

- "whose changes are these?"
- "the tree is dirty and it isn't mine"
- "sort out the pending changes"
- a second agent session, a colleague, or a CI-ish tool shares the checkout
- before cutting a branch from a tree whose modifications you did not make

It does not fire for your own uncommitted work, and it is unnecessary in a tree
nothing else writes to.

## Example

Seven dirty paths in a checkout two sessions share.

1. **Classify against the branch, not local `HEAD`.** Four come back `LANDED`:
   identical to `origin/develop`, and dirty only because the checkout had not
   been fast-forwarded. Nothing is lost by discarding those. Three are genuinely
   ahead. Expect this ratio; it is the reason the naive "commit everything" move
   creates so much noise.
2. **Check whether the writer has stopped, and treat the answer as advisory.**
   `stat` against `date` shows the newest file written eighteen minutes ago, and
   `lsof` shows nothing holding them. Neither proves nobody is writing, only that
   nothing was written recently, so the pull request records which checks were
   run rather than claiming the tree was quiet. Two other files share one
   timestamp to the second: not typed, but written in a sweep by a tool, which is
   worth knowing before attributing them to a person.
3. **Carry the work into a worktree cut from `origin/develop`**, never
   committing from the shared tree: tracked changes as a patch, so a deletion, a
   rename and a mode bit survive where `cp` would drop them, and untracked files
   copied alongside. Then `diff -q` each one.
4. **Re-check the source before pushing.** Unchanged, so the branch captures
   everything, and the pull request says so rather than assuming it.
5. **Say what you did not verify.** The claims came from someone else's session;
   the pull request marks them as recorded rather than reproduced.
6. **Re-classify before discarding.** After the merge the shared tree's copies
   are *stale*, not ahead: review findings improved them on the branch. The two
   states look identical to `git status`, so the direction of the diff decides
   whether discarding is safe.

## Why it is shaped like this

- **Both obvious moves are wrong.** Discarding destroys work nobody can recover;
  committing everything lands half-written edits under your name. The value is
  entirely in the classification step that neither move performs.
- **Stale and ahead are indistinguishable without asking.** After a rescue
  merges with review fixes on top, the shared tree still holds the pre-fix
  version, which `git status` reports exactly as it reported the original.
- **A one-line difference is the dangerous one.** It is usually a fix somebody
  landed deliberately, and copying the file over it reverts that fix invisibly:
  the resulting diff shows only additions.
- **It refuses rather than guesses.** A file still being edited, or one that does
  not parse, goes back to its author with what was found.

## Related

- `worktree-bootstrap`, for the opposite problem: a *fresh* worktree missing the
  ignored files and dependencies it needs to run.
- `branch-hygiene`, for the cleanup after the rescued branch merges.
- `prove-the-change-shipped`-style verification is what step 7 applies to the
  rescue itself: confirm the branch really supersedes the copy before discarding.
