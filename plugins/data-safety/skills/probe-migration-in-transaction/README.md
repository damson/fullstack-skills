# probe-migration-in-transaction

Applies a SQL migration inside a `begin` … `rollback` transaction against the
dev database and interrogates it as each role that will meet it, before the PR
opens, and without leaving a trace. The failure it prevents is the green that
means nothing: a policy that was never invoked because the table was empty, a
"refused" that was really an aborted transaction, a masking view that quietly
hands every row to every caller.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

Ask for it in any of these shapes; the skill fires on the intent, not on a
command:

- "what does this migration actually do?"
- "check the RLS policy before I open the PR"
- "probe the new view / trigger / grant against the dev database"
- a diff adds a migration whose effect is a behaviour: a policy, a view, a
  trigger, a grant, an enum, a constraint

It is built for the case where there is no local Postgres: a rolled-back
transaction against the dev database costs nothing and leaves nothing.

It deliberately does **not** fire for:

- a bulk data write you intend to keep; that is `reversible-bulk-write`
- a migration that only adds a column nothing reads yet
- a situation where the only reachable database is production; then it stops
  outright

## Example

The deliverable is a role × capability matrix for the PR body, with columns
derived from the migration's own statements and row counts as the unit:

| role | read | write | privileged column | direct table access |
|---|---|---|---|---|
| `pending` | 0 rows | 0 rows | NULL | refused |
| `volunteer` | 2,398 rows | 0 rows | NULL | refused |
| `admin` | 2,398 rows | 1 row | visible | refused |

Reading it: a write that *matched zero rows* and a write that was *refused* are
different answers: the first says the policy filtered every row, the second
says the grant held before the policy was consulted. The last column is the one
people omit: without it the matrix proves the front door is locked and says
nothing about the window.

Before the matrix is trusted, the skill breaks the migration on purpose in a
second transaction (stripping `security definer` or a `where` clause) and
confirms the probe that passed now fails. An assertion never observed failing
is decoration.

## Related

- `reversible-bulk-write` (this plugin): the counterpart for data writes meant
  to be kept; the two hand off to each other when a "migration" turns out to be
  data, or a "write" turns out to be structural.
- `supabase-ci-migration-guards` (this plugin): gets the same migration
  through a vanilla-Postgres CI before this skill probes what it does.
- `prove-the-check-can-fail` (verification plugin): step 8's break-it-on-purpose
  discipline is that skill's, applied to SQL.
