---
name: rewrite-pr-history
description: >
  Use when the user asks to drop, reorder or squash commits on a feature
  branch, rebase a branch onto a freshly-merged main, or otherwise rewrite
  history on an open PR. Do NOT fire on plain conflict resolution — merging
  the base branch forward fixes conflicts without a force-push and needs no
  rewrite. Bundles the safe rebase → verify →
  force-push-with-lease → PR-state-check cycle, including SSH-agent recovery
  and per-branch authorization gates.
---

# Rewrite PR history

When the user says "fix conflicts on PR N", "remove the X commit from PR N",
"rebase PR N onto main", "reorder commits on PR N", "drop the last commit",
or similar, run the procedure below.

The goal: never lose the user's work, never force-push to a shared branch,
never skip pre-flight checks. Every step is recoverable if interrupted.

## Procedure

### 1. Read PR state

```bash
gh pr view <N> --json baseRefName,headRefName,mergeable,mergeStateStatus,reviewDecision,commits
```

Confirm:
- Head branch is **not** `main`, `master`, `develop`, or any protected branch.
- Head branch is the user's to rewrite: only the user appears in
  `git shortlog -sn origin/<base>..HEAD`, and only one open PR has this head
  (`gh pr list --head <branch>`). Either check failing means the branch may
  be shared — ask before rewriting.
- If `reviewDecision` shows pending or approved reviews, surface that — review
  comments may go stale after a rewrite. Ask before continuing.

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
| Reorder / squash | `GIT_SEQUENCE_EDITOR=<script> git rebase -i origin/<base>` — see below; interactive `-i` without the wrapper needs terminal input agents don't have |
| Reword last commit only | `git commit --amend` (verify HEAD is the right commit first) |
| Split last commit | `git reset --soft HEAD~` then re-stage in parts |

The `GIT_SEQUENCE_EDITOR` script edits the todo file it is handed, e.g.
`sed -i '' 's/^pick <sha>/drop <sha>/' "$1"` — one mechanism for every
non-interactive reorder, drop or squash.

**If the rebase stops on a conflict**: resolve the conflicted files, `git add`
them, `git rebase --continue`; repeat per commit. If a resolution is not
obviously right, `git rebase --abort` returns the branch to its pre-rebase
state and the question goes to the user — an aborted rebase loses nothing.

Re-verify with `git log --oneline origin/<base>..HEAD` and
`git diff origin/<base> --stat` after every step, and confirm `git diff HEAD`
is empty — a non-empty diff there means something (an editor with the file
open, a merge tool) rewrote the working tree behind the rebase, and committing
would silently fold that change in.

### 5. Local checks before pushing

Run the project's documented test command. Detect it in this order:
1. `just --list` — use a recipe named `test`, `check`, or `verify` if present.
2. `package.json` — use the `scripts.test` value.
3. `Makefile` — use a `test` target if present.
4. Fall back to known project conventions: `bats tests/` for shell repos,
   `pytest` for Python, `cargo test` for Rust.

Also run the linter the repo CI uses (check `.github/workflows/` for hints —
`shellcheck`, `eslint`, `ruff`, etc.).

Don't push if checks fail — fix locally first.

### 6. SSH-agent pre-flight

```bash
ssh-add -l
```

If the agent has no identities, add the key the host uses (check `~/.ssh/config`
first; fall back to `~/.ssh/id_rsa` or `~/.ssh/id_ed25519`):

```bash
ssh-add ~/.ssh/<keyfile>
ssh -T git@github.com   # or git@gitlab.com
```

Confirm the auth message names the expected user before pushing.

### 7. Force-push with lease

```bash
git push --force-with-lease origin <branch>
```

**Never** use plain `--force`. `--force-with-lease` refuses to clobber if the
remote moved since the last fetch — if it rejects, stop and surface the diff
between expected and actual remote state.

### 8. Verify on the platform

```bash
gh pr view <N> --json mergeable,mergeStateStatus,commits -q \
  '{state:.mergeStateStatus,mergeable:.mergeable,commits:[.commits[].messageHeadline]}'
```

Confirm:
- `mergeable: MERGEABLE`
- `mergeStateStatus: CLEAN` (or `UNSTABLE` if CI is still running — that is OK)
- Commit list matches the planned outcome.

Report state back to the user.

## When to STOP

- **Branch is `main` or shared** → refuse. Suggest a revert PR or a forward-fix.
- **`--force-with-lease` is rejected** by remote → stop. Surface the diff,
  ask the user how to proceed. Do not switch to plain `--force`.
- **No explicit per-branch authorization for force-push** → ask. Prior
  authorization on one branch does not extend to another.
- **PR has approved reviews or unresolved comments** → ask before rewriting;
  reviewers may need to re-approve, and review comments anchor to commits.
- **CI was green and the rewrite is purely cosmetic** → ask if rewrite is worth
  the cache invalidation; sometimes a follow-up commit is better.
- **Working tree is dirty** → ask the user. Never silently stash.
