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
- The branch is yours to rewrite — checked, not assumed: only you appear in
  `git shortlog -sn origin/<base>..HEAD`, and only one open PR has this head
  (`gh pr list --head <branch>`). Either check failing means the branch may be
  shared — ask before rewriting; a rewrite under someone else's feet loses
  their work.
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
`"$1"` in place. Write the edit to a temporary file and move it over the
original rather than reaching for `sed -i`: the in-place flag takes a mandatory
empty argument on BSD (`sed -i ''`) and refuses one on GNU, so either spelling
is broken on half the machines that install this skill.

Resolve the commit to a real object id first, and export it: git writes object
ids in the todo file, so a literal `<sha>` matches nothing and the rebase
replays the branch unchanged, which looks like success.

```bash
export DROP=$(git rev-parse --short=7 <commit-to-drop>)
GIT_SEQUENCE_EDITOR='f() { sed "s/^pick $DROP/drop $DROP/" "$1" > "$1.todo" && mv "$1.todo" "$1"; }; f' \
  git rebase -i <base>
```

Seven characters on purpose: git abbreviates the todo's ids to whatever the
repository needs, and a seven-character prefix still matches a longer one, while
a full forty-character id matches nothing at all.

**If the rebase stops on a conflict**: resolve the conflicted files, `git add`
them, `git rebase --continue`; repeat per commit. If a resolution is not
obviously right, `git rebase --abort` returns the branch to its pre-rebase
state and the question goes to the user — an aborted rebase loses nothing.

Re-verify with `git log --oneline origin/<base>..HEAD` and
`git diff origin/<base> --stat` after every step, and confirm `git diff HEAD`
is empty — a non-empty diff there means something outside the rebase (an
editor with the file open, a merge tool) rewrote the working tree, and
committing would silently fold that change in.

### 5. Local checks before pushing

Run the project's documented test command. Detect it, never assume a toolchain:
a `test` / `check` / `verify` recipe in `just --list`, else `scripts.test` in
`package.json`, else a `test` target in the `Makefile`, else the language
default (`bats tests/`, `pytest`, `cargo test`, `go test ./...`). Also run the
linter the repo's CI uses (read `.github/workflows/` for hints); if no lint
step is discoverable in the CI config or the task runner, skip linting and say
so in the report — never stall on the search. Don't push if checks fail — fix
locally first.

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
