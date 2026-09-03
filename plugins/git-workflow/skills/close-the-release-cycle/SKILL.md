---
name: close-the-release-cycle
description: >
  Use when promoting an integration branch to the branch people install from, and
  when finishing one: "release it", "promote develop to main", "cut a release",
  "ship it", "tag it", or after a release PR merges. Fires on the whole cycle,
  not just the merge, because the failures live in the steps after it: an
  untagged release, a floating major tag left behind, and a skipped back-merge
  that makes the *next* promotion conflict. Do NOT fire for merging an ordinary
  feature PR into the integration branch.
---

# Close the release cycle

A release is not the merge. It is a cycle: promote, tag, move whatever floating
tag consumers follow, bring the promotion commit back, and confirm the branches
are level. Every step after the merge fails quietly, and the cost lands on
somebody else, one release later. This skill runs the cycle to completion and
refuses to call it done on a signal that has not been checked.

## Procedure

1. **Read the repo's own release policy before touching anything.** It decides
   two things this skill will not guess: whether a human merges the promotion,
   and whether the release is tagged by hand or by a workflow.

   ```bash
   ls docs/releas* RELEASING* CONTRIBUTING* 2>/dev/null
   grep -rln "release" .github/workflows/
   ```

   A repo that automates its own release is driven, not bypassed: dispatch its
   workflow rather than hand-rolling the steps below, then verify its output the
   same way.

2. **Confirm there is something to promote, by content and not by commit
   count.** After a promotion plus its back-merge, the integration branch is
   "ahead" by commits that carry nothing new.

   ```bash
   gh api repos/<owner>/<repo>/compare/<main>...<develop> \
     --jq '{status, ahead: .ahead_by, files: (.files | length)}'
   ```

   `status: identical`, or a files count of zero, means the release is empty:
   stop and say so.

3. **Merge the promotion with a merge commit, never a squash.** A squashed
   promotion puts a commit on the release branch that the integration branch
   holds no ancestor of. Trees still match, so nothing looks wrong until the
   *next* promotion opens as `CONFLICTING`, in a PR that has nothing to do with
   the mistake.

   ```bash
   gh pr merge <n> --merge
   ```

4. **Tag the release point, and check that it happened.** Tagging is the step
   most often lost, because the thing that swallows it reports success:
   **a merge performed on behalf of a CI token raises no push event**, so a
   workflow gated on a push to the release branch never runs. Nothing goes red.

   ```bash
   gh release list --limit 3            # is the new tag actually there?
   ```

   If a workflow owns tagging and did not fire, dispatch it rather than tagging
   by hand: a tag job worth its name is idempotent and is the repo's own
   definition of a release point.

5. **Move the floating tag consumers follow.** First find out whether the repo
   publishes one: a tag that is not a full version, sitting on an older commit
   than the newest release, is one.

   ```bash
   git ls-remote --tags <url> | grep -vE 'v?[0-9]+\.[0-9]+\.[0-9]+(\^\{\})?$'
   ```

   Nobody pinning it moves until you do, so a correctness fix stays undelivered
   while the release page says otherwise.

   ```bash
   sha=$(gh api repos/<owner>/<repo>/git/ref/tags/<vX.Y.Z> --jq .object.sha)
   gh api -X PATCH repos/<owner>/<repo>/git/refs/tags/<vX> -f sha="$sha" -F force=true
   ```

6. **Bring the promotion commit back.** It exists only on the release branch,
   and the branches drift from that moment on. Some repos open this PR
   automatically on a push to the release branch; check before opening a second.

   ```bash
   gh pr list --base <develop> --head <main> --json number --jq '.[].number'
   gh pr create --base <develop> --head <main> --title "Bring <main> back into <develop>"
   gh pr merge <n> --merge          # after its checks pass
   ```

7. **Prove the cycle closed** rather than assuming it. Three checks, and each
   one has caught a real omission:

   ```bash
   gh api repos/<owner>/<repo>/compare/<main>...<develop> --jq .status  # not "behind"
   gh release view <vX.Y.Z> --json tagName,targetCommitish
   gh api repos/<owner>/<repo>/git/ref/tags/<vX> --jq .object.sha       # == the release sha
   ```

8. **Update whatever pins this release.** Find the consumers rather than
   recalling them: search the owner's repositories for the released tag or the
   previous commit, and read what the release notes themselves promise about
   who moves with it.

   ```bash
   gh search code "<previous-sha-or-tag>" --owner <owner> --limit 100
   ```

   Then move each pin in its own change, with the evidence that earned the new
   commit: that is `bump-vendored-pin`'s job, and it also covers the case where
   the old pin no longer exists upstream. A release nobody consumes is half a
   release.

## Sharp edges

- **A red check on an auto-opened release or back-merge PR is often not about
  your code.** A PR opened by automation gets its checks queued seconds later,
  before the merge ref exists, and they fail with zero jobs and a message
  blaming the workflow file. The same commit is green on its push run. Read the
  job count before debugging: `gh api …/actions/runs/<id>/jobs --jq .total_count`.
- **The release branch is the one people install from**, so a badge, a version
  string or an install snippet that is only correct on the integration branch is
  wrong for every reader until the promotion lands. Check the rendered README on
  the release branch, not the working copy.

## When to STOP

- **The repo's policy says a human merges the promotion.** Prepare it, get it
  green, hand it over. Do not merge on a general instruction to release.
- **The comparison says `identical`.** There is nothing to release; say so
  rather than producing an empty release.
- **The promotion opens as `CONFLICTING`.** That is a previous cycle that was
  left open, not a problem with this one. Repair it first: merge the release
  branch into a branch off the integration branch, resolve in favour of the
  integration branch wherever the older squashed copy of a line won, and land
  that before promoting again.
- **A tag already points at the release commit.** It is done; re-tagging
  publishes a second release of the same tree.
