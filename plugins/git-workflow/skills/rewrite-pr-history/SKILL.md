---
name: rewrite-pr-history
description: >
  Use when deliberately editing the history of an open PR's branch — dropping,
  reordering, splitting or rewording commits, or squashing before review. Fire
  on "remove the X commit from PR N", "reorder the commits", "drop the last
  commit", "clean up the history before review". For the routine post-merge
  rebase of open PRs (duplicate commits after a parent landed), use
  branch-hygiene instead — that is mechanical cleanup, this is surgery.
---

# Rewrite PR history

The goal: never lose the user's work, never force-push a shared branch, and
show the plan before rewriting. Every step is recoverable if interrupted.

## Procedure

### 1. Read PR state

```bash
gh pr view <N> --json baseRefName,headRefName,mergeable,mergeStateStatus,reviewDecision,commits
```

Confirm:
- Head branch is **not** `main`, `master`, `develop`, or any protected branch.
- The branch is yours to rewrite. If other people push to it, ask before
  rewriting — a rewrite under someone else's feet loses their work.
- If `reviewDecision` shows pending or approved reviews, surface that — review
  comments anchor to commits and go stale after a rewrite. Ask before continuing.

### 2. Sync working tree

```bash
git fetch origin --prune
git checkout <head-branch>
```

Verify clean working tree (`git status -s` returns empty). If dirty, stop and
ask the user — never auto-stash without consent.

### 3. Show the plan

Run `git log --oneline origin/<base>..HEAD` and `git diff origin/<base> --stat`.
State the intended action in plain words (e.g. "I'll drop commit X by rebasing
--onto origin/main starting after it"). **Wait for explicit user "go"** before
rewriting.

### 4. Rewrite

Use the smallest-blast-radius command for the job:

| Goal | Command |
|---|---|
| Resolve conflicts with new main | `git rebase origin/main` |
| Drop one commit in the middle | `git rebase --onto <base> <commit-to-drop> <branch>` |
| Reorder / squash | non-interactive sequence edit, below — `git rebase -i` needs a terminal this environment does not have |
| Reword last commit only | `git commit --amend` (verify HEAD is the right commit first) |
| Split last commit | `git reset --soft HEAD~` then re-stage in parts |

Non-interactive drop/reorder: pipe the todo-list edit through the sequence
editor rather than a terminal —
`GIT_SEQUENCE_EDITOR=<script> git rebase -i <base>`, where the script edits
`"$1"` in place (e.g. `sed -i '' 's/^pick <sha>/drop <sha>/' "$1"`).

Re-verify with `git log --oneline origin/<base>..HEAD` and
`git diff origin/<base> --stat` after every step. Also check `git diff HEAD` — a
commit re-adding a line the base already has (different context) creates a
duplicate in the blob that tooling may silently drop from disk.

### 5. Local checks before pushing

Run the project's documented test command. Detect it, never assume a toolchain:
a `test` / `check` / `verify` recipe in `just --list`, else `scripts.test` in
`package.json`, else a `test` target in the `Makefile`, else the language
default (`bats tests/`, `pytest`, `cargo test`, `go test ./...`). Also run the
linter the repo's CI uses (read `.github/workflows/` for hints). Don't push if
checks fail — fix locally first.

### 6. Force-push with lease

```bash
git push --force-with-lease origin <branch>
```

**Never** plain `--force`. `--force-with-lease` refuses to clobber if the
remote moved since the last fetch — if it rejects, stop and surface the diff
between expected and actual remote state.

### 7. Verify on the platform

```bash
gh pr view <N> --json mergeable,mergeStateStatus,commits -q \
  '{state:.mergeStateStatus,mergeable:.mergeable,commits:[.commits[].messageHeadline]}'
```

Confirm `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN` (or `UNSTABLE` while
CI runs), and that the commit list matches the planned outcome. Report back.

## When to STOP

- **Branch is `main` or shared** → refuse. Suggest a revert PR or a forward-fix.
- **`--force-with-lease` is rejected** by the remote → stop, surface the diff,
  ask. Do not switch to plain `--force`.
- **No explicit per-branch authorization for the force-push** → ask. Prior
  authorization on one branch does not extend to another.
- **PR has approved reviews or unresolved comments** → ask before rewriting;
  reviewers may need to re-approve.
- **CI was green and the rewrite is purely cosmetic** → ask whether it is worth
  invalidating the run; sometimes a follow-up commit is better.
- **Working tree is dirty** → ask the user. Never silently stash.
