# await-pr-checks

Waits out a pull request's CI and returns a verdict that can be trusted: every
expected check named, judged at a pinned head SHA, with the failing step's log
already fetched when the answer is red.

Read [SKILL.md](SKILL.md) for the procedure. This file is why it exists.

## The three lies of a hand-rolled wait loop

All three were caught in one real session, from the same author, in one
afternoon:

- a queued check rendered as an **empty string**, slipped past a filter that
  only excluded `PENDING`-family words, and a failing run was reported green;
- a watcher started right after a push read the **previous run's** terminal
  state, because the new run had not registered yet;
- a loop that exited when "nothing is pending" could not say **whether it
  exited green or red**, and the report inherited the shrug.

The fix is not a cleverer one-liner. It is pinning the SHA before watching,
enumerating the checks you expect, treating empties as pending, and never
reporting a colour without the names behind it.

## Using it

It fires when a decision is waiting on a run, and before any report that
asserts a colour:

- "wait for the checks"
- "merge it when it goes green"
- "is CI green on 14?"
- "watch the run and tell me what broke"

It does not fire to *decide* anything: a green verdict authorises reporting,
never merging. That call stays where it was.

## Example

A pull request opened two minutes ago, read the moment the rollup is
available:

```console
$ gh pr view <n> --json statusCheckRollup \
    -q '[.statusCheckRollup[] | "\(.name // .context)=\(.conclusion // .state)"]'
["validate=", "CodeRabbit=PENDING"]
```

The first entry is the lie the skill exists for. `validate` has no conclusion
because the run is still going, and an empty string passes any filter written
to exclude the words `PENDING` and `IN_PROGRESS`. A loop built that way reports
the pull request settled while its only real check is still running.

Judged properly, both entries are pending and the wait continues. Four minutes
later the same command is terminal, and only then is there a verdict to quote:

```console
$ gh pr view <n> --json statusCheckRollup \
    -q '[.statusCheckRollup[] | "\(.name // .context)=\(.conclusion // .state)"]'
["validate=SUCCESS", "CodeRabbit=SUCCESS", "codecov/patch=SUCCESS", "codecov/project=SUCCESS"]
```

The report names all four. "Checks are green" would have been true here and
equally true in the first reading, which is what makes it worthless.

## Related

- `pr-comment-loop` (this plugin): what to do with the review once the run has
  settled.
- `merge-on-go-ahead` (this plugin): where the verdict is finally acted on,
  under an authorisation this skill deliberately does not assume.
- `diagnose-a-lying-signal` (verification plugin, if installed): the general
  case, for when the surface and the truth disagree anywhere else.
