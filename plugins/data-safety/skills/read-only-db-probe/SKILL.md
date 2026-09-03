---
name: read-only-db-probe
description: >
  Use when a claim needs numbers from a live database and no committed report
  already produces them — sizing a cohort before a design decision, verifying
  a reviewer's assertion against the data instead of arguing, checking what a
  load actually left behind. Produces a throwaway read-only script in the
  session scratchpad and quotes what it printed. Do NOT fire for anything
  that writes (that is reversible-bulk-write), or when the repo ships a
  report command that already answers the question — run that instead.
---

# Read-only probe against a live database

The deliverable is a number quoted from the probe's stdout — never from the
query looking right, and never from memory of a previous run.

## Procedure

1. **Check for an existing report first.** A repo that measures itself ships
   commands for the recurring questions (a queue-shape report, a health
   report). Re-deriving one of those by hand produces a second number that can
   disagree with the one everybody else quotes.

2. **Write the script to the session scratchpad** — its own step, never
   bundled into the shell call that runs it: a permission denial on a bundled
   call means the file was never written, and whatever runs next reads
   nothing, silently.

   The template. Every line is here because its absence has cost a session a
   retry:

   ```ts
   // Read-only: <the question this probe answers>
   import { pool } from '<absolute path to the repo's pool helper>';

   async function main() {           // scratchpad files transpile as CJS —
     const { rows } = await pool.query(`
       select count(*)::int as n from …
     `);                             // top-level await crashes, main() doesn't
     console.log(rows);
     await pool.end();               // or the process hangs, looking stuck
   }
   main().catch((e) => { console.error(e); process.exit(1); });
   ```

3. **Cast anything aggregated from catalog columns to `text`** —
   `array_agg(attname::text)`, not `array_agg(attname)`. Postgres drivers
   parse only the array types they know; `name[]` and friends arrive as the
   literal string `'{a,b}'`, and spreading a string silently yields its
   characters. The failure mode is an empty result that reads as "none
   found", not an error.

4. **Run it with the repo's env sourced by absolute path:**

   ```bash
   set -a; source /absolute/path/to/repo/.env; set +a
   npx tsx <scratchpad>/probe.ts
   ```

   Absolute, because the working directory resets between shell calls and a
   relative `source` that finds nothing leaves the connection string unset —
   which surfaces as a missing-variable error naming the right fix, at best.

5. **Quote the printed numbers.** If the probe informs a reply to a reviewer
   or a design decision, the stdout lines are the evidence — paste them, don't
   paraphrase them. A probe that produced a surprising number gets re-read for
   what it actually measured before the number gets used (a filter measuring
   presence-in-text is not a filter measuring headwords).

## When to STOP

- **The probe wants to write** — even "just a flag". Hand over to
  `reversible-bulk-write`: invariant first, dry-run, rollback before apply.
- **A committed report command answers the question** — run it; do not fork
  the truth.
- **The only reachable database is production and the query is heavy.** A
  `count(*)` is fine; a scan that would sit on a busy table during work hours
  is a conversation, not a probe.
