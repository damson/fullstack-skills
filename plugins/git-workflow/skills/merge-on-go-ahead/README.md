# merge-on-go-ahead

Presses the one button the neighbouring skills refuse to press, and only under
a permission that still applies. A checks watcher ends with "green authorises
reporting, not merging"; a review loop ends with "never merge from this skill".
Both are right, and between them sat an unwritten step that got improvised
every time: confirm the go-ahead covers this pull request at this commit, check
the gates the repository actually enforces, merge in the method that repository
prefers, and let a dependent pull request finish being recomputed before
touching it.

The failure it prevents is not a merge that breaks. It is a merge that looks
perfectly ordinary: the right button on a head commit the reviewer never saw,
or in a style the project forbids, or over a review whose findings nobody
answered.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

It fires on an authorisation that names pull requests:

- "merge 12"
- "14 and 15 are ready to go"
- "land 21, the checks are green"
- "go ahead" in a thread about one identified pull request

It deliberately does **not** fire on:

- "looks good", an approving review, or a go-ahead given for a different pull
  request; authorisation is per pull request and does not roll forward
- a promotion into the branch people install from, which has steps after the
  merge and belongs to `close-the-release-cycle`
- the question of whether something *should* merge; it does not weigh a change

## Example

Two pull requests are authorised, the second stacked on the first.

The skill pins both heads and finds the first still at the commit that was
reviewed, keeping that SHA for the merge command itself. It reads the rules in
force on the base rather than the rendered checks list, because a summary that
says "1 failing" is often a job named for the failure it is supposed to force,
and because the rule on a base frequently allows exactly one merge method,
which settles a question the repository-level settings leave open. It confirms
the review reply exists and squashes the first with `--match-head-commit`, so a
commit pushed in the meantime refuses the merge instead of riding in on an
authorisation given for something else.

The child is dealt with before the parent moves, not after: a stacked pull
request does not follow its parent through a merge, it is left pointing at a
branch nobody will push to again. Then the skill waits. Immediately after the
parent lands, the child's `mergeable` reads `UNKNOWN`, which is not `false`,
and a decision taken on that value is a coin toss. The wait is bounded and
treats a failed read as a failed read: a bare command substitution turns an API
error into an empty string, which is also not `UNKNOWN`, and the loop would
exit on it looking satisfied.

Landing is confirmed with the merge commit, not the branch tip. A squash is not
the commits it squashed, so asking whether the head is an ancestor of the base
reports fully merged work as unmerged: on a real PR here, the head answered
"no" while the recorded merge commit answered "yes" against the same branch.

The report names the method, because "merged" alone does not distinguish the
one that keeps the history the next promotion needs from the one that breaks
it.

## Related

- `await-pr-checks` (this plugin): the verdict this one waits on, including the
  reruns and empty conclusions a hand-rolled loop misreads.
- `pr-comment-loop` (this plugin): answers the review; it hands the button
  back, and this skill is what receives it.
- `branch-hygiene` (this plugin): what happens to the branch and its worktree
  once the merge is proved.
- `close-the-release-cycle` (this plugin): the promotion case, where the merge
  is the middle of the procedure rather than the end.
