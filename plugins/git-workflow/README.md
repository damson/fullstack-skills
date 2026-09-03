# git-workflow

Branch, worktree and pull-request hygiene: twelve skills for the moments where
git and GitHub quietly do something other than what everyone at the keyboard
believed.

```bash
claude plugin install git-workflow@hard-won-skills --yes
```

The family resemblance: each of these failures *looks* fine from the outside.
A squash-merged branch reads as unmerged forever, so cleanup silently skips it.
A child PR keeps running checks against a branch nobody will push to again. A
screenshot renders for you (authenticated) and breaks for every reviewer. A
scheduled workflow merged to the wrong branch is simply never registered, and
nothing errors. These skills exist because someone watched each of those
happen.

## The skills

| Skill | What it does |
|---|---|
| [`branch-hygiene`](skills/branch-hygiene/README.md) | After a merge: retarget children first, rebase the open PRs, prune branches and worktrees by PR state, close the issues the keywords could not |
| [`pr-comment-loop`](skills/pr-comment-loop/README.md) | Verify review findings against the source, then answer them: one sticky comment, one row per finding, unambiguous verdicts |
| [`rewrite-pr-history`](skills/rewrite-pr-history/README.md) | Deliberate history surgery on an open PR (drop, reorder, split, reword), with the plan shown before anything moves |
| [`worktree-bootstrap`](skills/worktree-bootstrap/README.md) | Make a fresh worktree actually run: carry the gitignored config over from a donor, rebuild the per-tree dependencies |
| [`capture-pr-screenshots`](skills/capture-pr-screenshots/README.md) | From "the diff touched a UI page" to a SHA-pinned image in the PR body, without capturing the login form by mistake |
| [`github-pr-screenshot-embed`](skills/github-pr-screenshot-embed/README.md) | The one host rule that keeps an embedded image rendering for reviewers on a private repo |
| [`audit-diagram-claims`](skills/audit-diagram-claims/README.md) | Treat every diagram node as a set of claims and check each against reality before ticking "architecture updated" |
| [`coverage-pr-comment`](skills/coverage-pr-comment/README.md) | Coverage as one sticky comment with a delta and a threshold band, instead of a bare percentage nobody acts on |
| [`await-pr-checks`](skills/await-pr-checks/README.md) | Wait out a PR's CI at a pinned SHA and report a per-check verdict: an empty conclusion is pending, never passing |
| [`parallel-pr-fanout`](skills/parallel-pr-fanout/README.md) | Land a batch of independent fixes as file-disjoint PRs built by parallel agents, with briefs and scope fences that hold |
| [`bump-vendored-pin`](skills/bump-vendored-pin/README.md) | Move a pinned vendored dependency only with the evidence that earned the new commit |
| [`wire-scheduled-workflow`](skills/wire-scheduled-workflow/README.md) | Check a cron workflow is actually registered: GitHub only arms schedules from the default branch |

Each skill's README carries its triggers and a worked example; the `SKILL.md`
beside it is the procedure the agent follows.
