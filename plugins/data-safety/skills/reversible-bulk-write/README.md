# reversible-bulk-write

Puts three things in place before a bulk write touches a live datastore: a
measured invariant that must not move, a dry run of every stage, and a rollback
written and schema-checked while nothing is broken yet. The failure it
prevents is discovering the rollback's typo, or the marker that also matches
rows you did not create, after the bad data is already live.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

Ask for it in any of these shapes; the skill fires on the intent, not on a
command:

- "import this dataset into the live database"
- "backfill the column for every existing row"
- a mass `UPDATE`, or any statement whose blast radius is "lots of rows"
- "that bulk write went wrong, undo it" (it also covers the after case)

It fires **before the first write**, not after it goes wrong.

It deliberately does **not** fire for:

- ordinary single-row writes
- schema migrations; those have their own review and apply path
  (`probe-migration-in-transaction` is the probe for them)
- writes to a throwaway or local database

## Example

The deliverable is a report of both numbers, not an adjective:

> Queue 598 → 2,371, `entries` unchanged at 1,541.

That is a verifiable claim; "imported successfully" is not. The invariant
(`entries` stays 1,541) was recorded *before* the write; the projected count
(2,371) came from a dry run of every stage before any stage applied; and the
rollback existed first, scoped to what this operation created (a batch id, an
`intake_source`, a timestamp window), never a bare `delete from <table>`.

Two of its sharp edges show up in almost every import: a file labelled "new
candidates" is only new against whatever existed when it was written, so
novelty is re-checked against the live target; and an interrupted write leaves
a partial state, so the job is stopped and rolled back explicitly rather than
assumed atomic.

## Related

- `probe-migration-in-transaction` (this plugin): the counterpart for
  structural changes; each skill's do-not-fire list names the other.
- `pre-publication-sweep` (this plugin): the same "no undo" reasoning applied
  to publishing rather than writing.
- `prove-the-check-can-fail` (verification plugin): the same suspicion of
  counts that look too clean, applied to checks instead of writes.
