# parallel-pr-fanout

Turns a batch of independent fixes into separate, reviewable pull requests
built by parallel agents: partitioned so no two agents touch the same file,
briefed with the facts they cannot discover, and fenced so out-of-scope
findings become flagged follow-ups instead of surprise diffs.

Read [SKILL.md](SKILL.md) for the procedure. This file is why the partition
comes first.

## Why file ownership, not topics

Topics overlap in files the topic names forget: the script table in the
architecture doc, the shared test helper, the README section a change
falsifies. In the session this skill was extracted from, ten PRs merged in
arbitrary order without a single conflict, because the partition was done on
files, the fences held (three agents reported out-of-scope findings in their
PR bodies instead of fixing them), and every brief carried the `file:line`
findings the agent could not have re-derived alone.

Generic dispatch mechanics (when to parallelise at all, how many agents) are a
separate concern; this skill is only the PR-batch discipline on top.

## Using it

It fires when three or more independent changes should land as separate,
reviewable pull requests:

- "address all of these"
- "fix everything on the list"
- "make as much parallel work as possible"
- a review or an eval that produced many unrelated fixes

It does not fire for coupled changes, which are one pull request; for
sequential work, which is a stack; or for parallelism that produces no pull
requests, which is plain agent dispatch. The partition is the skill, and the
agents are only what runs it.

## Example

An evaluation returns 31 findings spread across five plugins. Topic-shaped
work would have every agent editing the same two README files and racing on
version numbers.

Partitioned by file ownership instead, each agent owns one plugin's tree and
nothing else, and each brief carries the `file:line` findings for that tree
plus the facts the agent cannot discover: which conventions the repository
enforces, what has already been ruled out, and that no attribution footer or
session link goes in a commit or a pull request body.

Five pull requests come back, one per plugin. The fence is checked before each
push (`git diff --name-only origin/<base>...HEAD`, compared against the agent's
allowed set) and every one comes back clean. Disjoint files are necessary but
not sufficient, so the couplings that share no path are checked too, a
generated file and its source, a producer and its consumer, a migration; with
those clear, the five merge in any order. Findings outside an agent's tree
arrive as flagged follow-ups in the pull request body rather than as surprise
diffs, which is what keeps the partition honest under pressure.

## Related

- `pr-comment-loop` (this plugin): each of those pull requests still needs its
  review answered, one row per finding.
- `merge-on-go-ahead` (this plugin): a batch authorised together still merges
  one at a time.
- `branch-hygiene` (this plugin): five branches and five worktrees to prune
  afterwards, by pull request state rather than by ancestry.
