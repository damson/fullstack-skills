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
