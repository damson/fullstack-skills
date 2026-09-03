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
