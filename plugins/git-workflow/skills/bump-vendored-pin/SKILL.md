---
name: bump-vendored-pin
description: >
  Use when moving a pinned vendored dependency to a new upstream commit — a
  git submodule gitlink, a GitHub Action's pinned ref, a SHA recorded in a
  config file. Fires on "bump the pin", "update the submodule", after an
  upstream merge lands, and after an upstream history rewrite orphans the old
  SHA. Do NOT fire for floating refs (a branch name or `@main` is not a pin),
  or when the vendored copy is being edited in place — that is a different
  mistake, and the fix is upstreaming the edit, not bumping.
---

# Bump a vendored pin

A pin is a claim: *this exact commit was reviewed and works here.* Moving it
without re-earning the claim leaves every consumer running untested code that
still looks pinned. The deliverable is the new SHA plus the evidence that
earned it — a test count or a tree identity, cited in the commit.

## Procedure

1. **Resolve the new SHA from the upstream remote**, not from a local clone:
   `git ls-remote <url> <branch>`. A clone can be stale in either direction,
   and a stale one fails silently — it hands you a real SHA that is simply not
   the one you meant.

2. **Name what the move contains**: `git log --oneline <old>..<new>` in the
   upstream. If that range errors because the old SHA no longer exists, the
   upstream history was rewritten — go to step 3, because "what changed" has a
   different answer than the log.

3. **After an upstream rewrite, prove what survived**:
   `git rev-parse <old>^{tree} <new>^{tree}`. Identical trees mean the rewrite
   changed commit identity only — cite the tree hash as the review evidence.
   Different trees mean the rewrite smuggled in content; diff it before
   trusting it.

4. **Find every pin, not just the one you came for.** Gitlinks
   (`git submodule status`), action defaults, refs in workflows and config:
   `grep -rn <old-sha>` across the repo. A repo that pins in two places
   updates one and drifts in the other, and the drift is invisible until the
   stale pin executes.

5. **Run the vendored copy's own test suite at the new pin, from the
   consumer's checkout** — that is the copy that will actually execute, and it
   is what catches a bump to a broken commit before anything depends on it.
   The command is whatever the vendored repo's own CI runs — read its workflow
   file rather than guessing at `make test` vs `bats` vs `just`.

6. **Commit the pin move alone**, with the evidence in the message. A pin bump
   folded into a feature commit cannot be reverted without reverting the
   feature.

## When to STOP

- **The upstream suite fails at the new pin** — report it; never pin a broken
  commit "to fix forward later".
- **The new SHA is not a descendant and the trees differ** — you may be about
  to pin a fork, a rollback, or the wrong remote; confirm intent first.
- **`git ls-remote` cannot reach the upstream** (auth, deletion, rename) —
  resolve access first; a pin moved from memory or a stale clone is a guess.
- **The old SHA appears in more places than one change can update** (other
  repos, published docs) — surface the full list before moving any of them.
