---
name: merge-on-go-ahead
description: >
  Use when the user authorises merging pull requests they name: "merge #4",
  "12 and 13 are ready", "land 21 and 22", or a bare "go ahead" in a thread
  about one identified PR. Owns only the merge itself: it confirms the authorisation covers
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
   head=$(gh pr view <n> --json headRefOid --jq .headRefOid)   # step 6 merges against this
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
   gh api repos/<owner>/<repo>/rules/branches/<base>          # rules in force here
   ```

   Two sources, because either can be empty while the other gates. A branch
   with no classic protection answers the first call with `404 Branch not
   protected`, which is an answer (nothing is required here), not a failure to
   route around. The second is the one to trust for rulesets: a repository-wide
   listing tells you a ruleset exists, while this endpoint tells you which
   rules apply to *this* base, with their parameters.

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
   gh api repos/<owner>/<repo>/rules/branches/<base> \
     --jq '.[] | select(.type == "pull_request") | .parameters.allowed_merge_methods'
   grep -rniE "squash|merge commit" CONTRIBUTING* docs/ .github/ 2>/dev/null | head
   ```

   The three answers are not the same question. The first is what the
   repository *permits* anywhere, the second is what a rule *allows on this
   base* (often exactly one method, which settles it), the third is what the
   project says it prefers where the rules leave a choice.

   Repos that allow several are the dangerous ones: allowed is not preferred,
   and the preference is usually written down. A project can also want
   different methods for different bases, most often a squash into the
   integration branch and a merge commit for the promotion, because a squash
   is not the commits it squashed and breaks the ancestry the next step relies
   on.

5. **Deal with anything stacked on this PR before merging it.** A child whose
   base is this branch does not follow the parent through the merge; it is left
   pointing at a branch nobody will push to again, and its checks keep running
   against it. Retarget the children first, or delete the parent branch as part
   of the merge if that is what retargets them on this host. Polling a child's
   mergeability does not repair a stale base, and `branch-hygiene` owns the
   full post-merge sequence.

6. **Merge one at a time, in the stated method, bound to the authorised head.**
   Let the merge command own the line it runs on: some tool wrappers classify a
   chained merge differently from a bare one, and a merge refused halfway
   through a compound command is harder to reason about than one that simply
   ran.

   ```bash
   gh pr merge <n> --squash --match-head-commit "$head"   # or --merge, per step 4
   ```

   `--match-head-commit` is step 1's pin made mechanical: if anything was
   pushed between the go-ahead and this command, the merge is refused instead
   of quietly landing a commit nobody authorised.

7. **Between dependent merges, wait for the recomputation, and do not read a
   failure as an answer.** After a parent lands, a child's `mergeable` reads
   `UNKNOWN` until the host recomputes it, and `UNKNOWN` is not `false`. A bare
   command substitution in the loop test turns a failed API call into an empty
   string, which is also not `UNKNOWN`, so the loop exits on the error:

   ```bash
   for _ in $(seq 1 24); do
     state=$(gh pr view <child> --json mergeable --jq .mergeable) || state=
     [ -n "$state" ] && [ "$state" != "UNKNOWN" ] && break
     sleep 5
   done
   [ -n "$state" ] && [ "$state" != "UNKNOWN" ] || { echo "mergeability never settled"; exit 1; }
   ```

   Acting on the interim value either merges something the host has not
   finished judging, or abandons a PR that was fine two seconds later.

8. **Prove it landed with the merge commit, not the branch tip.** A squash
   produces a commit that is not the branch's commits, so asking whether the
   *head* is an ancestor of the base answers "not merged" for work that is
   fully merged. The merge commit the host recorded is on the base, so ask
   about that one:

   ```bash
   git fetch --prune
   mc=$(gh pr view <n> --json mergeCommit --jq .mergeCommit.oid)
   git merge-base --is-ancestor "$mc" origin/<base> && echo landed
   ```

   Where no merge commit is recorded (a PR closed and applied by hand), fall
   back to content: capture the paths **before** merging
   (`git diff --name-only origin/<base>...origin/<branch>`) and compare them
   against the fetched head ref (`refs/pull/<n>/head`) afterwards, since the
   branch itself may be gone. Read that comparison the same day: once another
   PR touches those paths, a difference stops meaning anything about this one.

9. **Report per PR, naming the method**: `#12 squashed into develop, #13
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
