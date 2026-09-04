---
name: merge-on-go-ahead
description: >
  Use when the user authorises merging specific pull requests: "merge #4",
  "12 and 13 are ready", "go ahead and land it", "ship the ones that are
  green". Owns only the merge itself: it confirms the authorisation covers
  this PR at its current head, checks the gates the repo actually enforces,
  merges in the repo's own convention, and waits out the recomputation
  before touching a dependent PR. Do NOT fire without an authorisation
  naming the PRs, on a promotion to the branch people install from (that is
  a release), or to decide WHETHER something should merge.
---

# Merge on a go-ahead

Merging is the one step in a pull request's life that cannot be undone quietly.
Every neighbouring procedure stops at this line on purpose: a checks watcher
authorises reporting, not merging, and a review loop answers findings and hands
the button back. This skill picks up exactly there, and it starts by proving the
permission still applies rather than assuming the last one carried forward.

The failure it prevents is not a broken merge. It is a *correct-looking* one:
the right button pressed on a PR whose head moved after the go-ahead, or in a
merge style the repo forbids, or while a review sits unanswered.

## Procedure

1. **Bind the authorisation to a PR and a commit.** Write down which numbers
   were named, then pin each head:

   ```bash
   gh pr view <n> --json number,headRefOid,baseRefName,isDraft,mergeable,mergeStateStatus
   ```

   An authorisation is per pull request and per head. It does not roll forward
   to a sibling PR, to the next one in a stack, or to a new commit pushed after
   it was given, however small. If the head moved, the go-ahead was for
   something the reader no longer sees; say so and ask again.

2. **Confirm the gates the repo enforces, not the ones you remember.** Read the
   required contexts rather than eyeballing a checks list:

   ```bash
   gh api repos/<owner>/<repo>/branches/<base>/protection \
     --jq '.required_status_checks.contexts'
   gh api repos/<owner>/<repo>/rulesets --jq '.[] | "\(.name) \(.enforcement)"'
   ```

   A branch with no protection answers that first call with `404 Branch not
   protected`, which is an answer (nothing is required here), not a failure to
   route around: read it, then rely on the ruleset and the repo's own written
   policy instead.

   Judge each check by `status` and `conclusion` per the checks-watching
   discipline (`await-pr-checks` covers it, including the reruns and the
   unpinned reads). Counting the word "fail" in a rendered checks list is not
   judging it: job names contain that word on purpose, and a suite whose whole
   point is a must-fail case reports itself as one.

3. **Confirm the review gate is answered, not merely present.** Where the repo
   requires a review before merge, an automated one that posted findings still
   needs the reply that dispositions them (`pr-comment-loop` owns that loop).
   A merge on top of an unanswered review erases the finding and the record of
   why it was ignored, in one action.

4. **Look the merge method up. Do not carry it between repos.**

   ```bash
   gh api repos/<owner>/<repo> --jq '{squash: .allow_squash_merge, merge: .allow_merge_commit, rebase: .allow_rebase_merge}'
   grep -rniE "squash|merge commit" CONTRIBUTING* docs/ .github/ 2>/dev/null | head
   ```

   Repos that allow several are the dangerous ones: allowed is not preferred,
   and the preference is usually written down. A project can also want
   different methods for different bases, most often a squash into the
   integration branch and a merge commit for the promotion, because a squash
   is not the commits it squashed and breaks the ancestry the next step relies
   on.

5. **Merge one at a time, in the stated method**, and let the command own the
   line it runs on. Some tool wrappers classify a chained merge differently
   from a bare one, and a merge that is refused halfway through a compound
   command is harder to reason about than one that simply ran:

   ```bash
   gh pr merge <n> --squash    # or --merge, per step 4
   ```

6. **Between dependent merges, wait for the recomputation.** After a parent
   lands, a child's `mergeable` reads `UNKNOWN` until the host recomputes it,
   and `UNKNOWN` is not `false`:

   ```bash
   until [ "$(gh pr view <child> --json mergeable --jq .mergeable)" != "UNKNOWN" ]; do sleep 5; done
   gh pr view <child> --json mergeable,mergeStateStatus
   ```

   Acting on the interim value either merges something the host has not
   finished judging, or abandons a PR that was fine two seconds later.

7. **Prove it landed by content, not by ancestry.** A squash merge produces a
   commit that is not the branch's commits, so `git merge-base --is-ancestor`
   answers "not merged" for work that is fully merged. Compare what the branch
   changed against the base instead:

   ```bash
   git fetch --prune
   git diff --stat origin/<base> origin/<branch> -- <paths the branch touched>
   ```

   Empty output for those paths is the landing proof; ancestry is not.

8. **Report per PR, naming the method**: `#12 squashed into develop, #13
   squashed, both branches deleted`. Cleaning up the merged branches and their
   worktrees is its own procedure (`branch-hygiene`); a promotion to the branch
   people install from is a release cycle, not a merge, and belongs to
   `close-the-release-cycle`.

## When to STOP

- **No authorisation names this PR.** "Looks good", an approving review, or a
  go-ahead given for a different PR is not one. Report the PR as ready and stop.
- **The head moved after the authorisation.** Re-ask against the new commit
  rather than deciding the change was too small to matter.
- **A required check is missing rather than failing.** Absent and passing look
  identical in a summary and are opposites; treat missing as pending.
- **A review posted findings that have no reply.** Answer them first, or hand
  back; merging closes the thread by force.
- **The repo allows several merge methods and states no preference.** Ask which
  one. Guessing here is the one mistake in this procedure that rewrites history
  for everybody.
- **The base is the branch people install from.** That is a promotion with
  steps after the merge (tag, floating tag, back-merge) and a different owner.
- **The merge is refused for a reason you did not diagnose** (protection, a
  queue, a conflict). Report the refusal with its message; retrying a blocked
  merge with a different flag is how a rule gets worked around instead of read.
