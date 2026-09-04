# read-only-db-probe

Writes a throwaway read-only script into the session scratchpad, runs it
against the live database, and quotes what it printed. The failure it
prevents is the confident number nobody measured: a cohort sized from memory,
a reviewer's claim answered with an argument when the data was one query
away, an "empty result" that was really a driver handing back an unparsed
string.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

Ask for it in any of these shapes; the skill fires on the intent, not on a
command:

- "how many rows would that actually affect?"
- "is the reviewer right about this? check the data"
- "did the load land? read it back"
- a design decision is about to be made on a number nobody has measured

It deliberately does **not** fire for:

- anything that writes, even a single flag; that is `reversible-bulk-write`
- a question the repo's own report commands already answer
- heavy scans against a production-only database

## Example

Sizing a backfill before writing it. The table holds 1,200 entries; the
question is how many are missing `part_of_speech`, and how many of those
someone has already reviewed. One file in the scratchpad, in the template's
shape:

```ts
// Read-only: how many entries would a part_of_speech backfill touch?
import { pool } from '/absolute/path/to/repo/db'

async function main() {
  const { rows } = await pool.query(`
    select count(*)::int                                        as missing_pos,
           count(*) filter (where reviewed_at is not null)::int as already_reviewed
    from entries
    where part_of_speech is null
  `)
  console.log(rows)
  await pool.end()
}
main().catch((e) => { console.error(e); process.exit(1); })
```

Run it with the env sourced by absolute path, and quote what it printed:

```console
$ set -a; source /absolute/path/to/repo/.env; set +a
$ npx tsx probe.ts
[ { missing_pos: 400, already_reviewed: 80 } ]
```

That line is the deliverable, not "a few hundred". 400 is the candidate count,
and the 80 are a subset of it: rows missing `part_of_speech` that someone has
already reviewed. So a blind `update` writes 400 rows and overwrites those 80;
a backfill that preserves reviewed work writes 320. One total would have hidden
the difference, and the difference is the whole decision.

The `::text` in step 3 is not folklore. A second probe, same connection, same
driver (`pg`, node-postgres), asks for the column names both ways:

```ts
const { rows } = await pool.query(`
  select array_agg(attname)       as raw,
         array_agg(attname::text) as cast
  from pg_attribute
  where attrelid = 'entries'::regclass and attnum > 0
`)
const { raw, cast } = rows[0]
console.log('raw  typeof:', typeof raw,  'value:', raw)
console.log('cast typeof:', typeof cast, 'value:', cast)
console.log('spread raw :', [...raw].slice(0, 6))
```

```console
raw  typeof: string value: {id,headword,part_of_speech,reviewed_at}
cast typeof: object value: [ 'id', 'headword', 'part_of_speech', 'reviewed_at' ]
spread raw : [ '{', 'i', 'd', ',', 'h', 'e' ]
```

Uncast, `array_agg(attname)` arrives as a single string. Spread it and you get
characters, so a membership test against it matches nothing while reading
exactly like "the column is not there".

## What the template already survived

Three failures are baked into the template because each cost a real session a
retry: scratchpad scripts transpile as CJS, so top-level `await` crashes and
the body lives in `main()`; a forgotten `pool.end()` hangs the process in a
way that reads as a slow query; and catalog arrays (`name[]`) arrive as the
literal string `'{a,b}'` unless cast to `text` inside the aggregate; spread
that uncast string and it silently yields its characters and an empty match
that looks exactly like "nothing found".

## Related

- `reversible-bulk-write` (this plugin): where the probe hands off the moment
  the question turns into a write; the numbers above are what its dry run is
  checked against.
- `probe-migration-in-transaction` (this plugin): the same read-first
  discipline for structural change rather than data.
- `diagnose-a-lying-signal` (verification plugin, if installed): the wider
  version of the empty result that was never a result.
