# bump-vendored-pin

Moves a pinned vendored dependency (a submodule gitlink, a pinned Action ref,
a SHA in a config file) without losing what the pin meant. A pin is a claim:
*this exact commit was reviewed and works here.* Moving it without re-earning
that claim leaves every consumer running untested code that still looks pinned.
The deliverable is the new SHA **plus the evidence that earned it**, cited in
the commit message.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

- "bump the pin"
- "update the submodule"
- after an upstream merge lands
- after an upstream history rewrite orphans the old SHA

It does not fire for floating refs (a branch name or `@main` is not a pin),
nor when the vendored copy is being edited in place; that is a different
mistake, and the fix is upstreaming the edit, not bumping.

## Example

An upstream repo rewrote its history and the vendored pin now points at a SHA
that no longer exists. The skill:

1. Resolves the new SHA from the upstream **remote** (`git ls-remote <url>
   <branch>`), never a local clone, which can be stale in either direction and
   fails silently by handing you a real SHA that is not the one you meant.
2. Fetches the upstream objects (`ls-remote` resolved a name without
   downloading anything), then tries `git log --oneline <old>..<new>` to name
   what the move contains, backed by `git merge-base --is-ancestor <old>
   <new>`: a surviving local copy of the old SHA can make the range succeed
   against a rewritten upstream. Here the ancestry check fails (the old SHA
   is gone from upstream), so the answer comes from tree identity instead:

   ```bash
   git rev-parse <old>^{tree} <new>^{tree}
   ```

   Identical trees mean the rewrite changed commit identity only; the tree
   hash *is* the review evidence. Different trees mean the rewrite smuggled in
   content; diff it before trusting it.
3. Finds every pin, not just the one it came for (`grep -rn <old-sha>` across
   the repo), because a repo that pins in two places updates one and drifts in
   the other, invisibly, until the stale pin executes. After a history
   rewrite the sweep widens to every consumer repo: each one breaks with the
   same distinctive `upload-pack: not our ref` fetch error, and each pin
   moves with its own change. A dead submodule pin is recovered from inside
   the submodule — fetch a live branch there, check out the new SHA, stage the
   gitlink — and consumers the checkout cannot see are found with a forge-wide
   code search for the old SHA, or reported as unchecked when even that is
   unavailable. When no copy of the old commit survives, the commit message
   says the range is not diffable and the suite run carries the review.
4. Runs the vendored copy's own test suite at the new pin, from the consumer's
   checkout, using whatever the vendored repo's own CI runs.
5. Commits the pin move alone, evidence in the message: a bump folded into a
   feature commit cannot be reverted without reverting the feature.

If the upstream suite fails at the new pin, the answer is a report, never a
broken pin "to fix forward later".

## Related

- `verification` plugin's `verify-dependency-behaviour`: when the question is
  not "which commit" but "what does this dependency actually do".
- `wire-scheduled-workflow`: pinned Action refs live in the same workflow
  files that skill wires up.
