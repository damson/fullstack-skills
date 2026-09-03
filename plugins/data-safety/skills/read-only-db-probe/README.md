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

## What the template already survived

Three failures are baked into the template because each cost a real session a
retry: scratchpad scripts transpile as CJS, so top-level `await` crashes and
the body lives in `main()`; a forgotten `pool.end()` hangs the process in a
way that reads as a slow query; and catalog arrays (`name[]`) arrive as the
literal string `'{a,b}'` unless cast to `text` inside the aggregate; spread
that uncast string and it silently yields its characters and an empty match
that looks exactly like "nothing found".
