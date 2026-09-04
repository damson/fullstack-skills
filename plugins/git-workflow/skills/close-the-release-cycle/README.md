# close-the-release-cycle

Runs a release to completion instead of to the merge: promote, tag, move the
floating tag consumers follow, back-merge, then prove each of those actually
happened. The failure it prevents is a release that looks finished and is not,
because every step after the merge fails without turning anything red.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

Say any of these; the skill fires on the intent, not on a command:

- "release it"
- "promote develop to main"
- "cut a release"
- "tag it"

It also fires **after a release PR merges**, which is the moment the rest of the
cycle gets forgotten. It stays quiet for an ordinary feature PR landing on the
integration branch, since none of the tagging or back-merge steps apply there.

## The three failures it exists for

**An untagged release.** A promotion merged by automation lands as the CI
token, and a merge by that token raises no push event, so the workflow that
tags the release never runs. Nothing is red, the release page simply has no new
entry. The skill checks `gh release list` rather than trusting the merge.

**A floating tag left behind.** Consumers pinning `v1` keep getting the old
commit until the tag is moved, so a fix ships and does not arrive. Moving it is
one `PATCH` with `force=true`, and it is invisible if skipped.

**A skipped or squashed back-merge.** A promotion merged with `--squash` puts a
commit on the release branch that the integration branch holds no ancestor of.
Both trees still match, so nothing looks wrong until the *next* promotion opens
as `CONFLICTING`, one release later, in a PR unrelated to the mistake. The skill
merges promotions with a merge commit and treats a conflicting promotion as
evidence of an earlier unclosed cycle.

## Example

```
> release it

Repo policy: releases are tagged by a workflow, promotion merged by a human.
Comparison: ahead by 4 commits, 11 files. Not empty.
Release PR #29 is green. Policy says you merge it, so it is ready and waiting.

[after the merge]
Merged. Release list still shows v1.1.0 as latest, so the tag job did not fire:
auto-merge as the CI token raises no push event. Dispatching the tag workflow.
v1.1.1 published, v1 moved to the same commit, back-merge #30 merged.
Branches level, tag targets the release commit. Cycle closed.
```

## What it will not do

It will not merge a promotion in a repo whose policy reserves that for a human,
will not produce an empty release when the branches are already identical, and
will not re-tag a commit that is already a release point.

## Related

- `wire-scheduled-workflow` (this plugin): the cron that starts this cycle is
  only armed from the default branch, which is its own silent failure.
- `merge-on-go-ahead` (this plugin): the ordinary feature merge, which stops at
  the merge because nothing follows it.
- `bump-vendored-pin` (this plugin): the other place a tag is the thing being
  moved, with the evidence that earned it.
- `prove-the-check-can-fail` (verification plugin, if installed): the habit
  behind every "and prove each one happened" in this procedure.
