# supabase-ci-migration-guards

Gets a migration that references Supabase-managed schemas (`auth.*`,
`storage.*`, `realtime.*`) through a CI that runs vanilla Postgres — where none
of those schemas exist. The failure it prevents costs one fix commit and one CI
cycle each time: `schema "auth" does not exist`, `relation "storage.objects"
does not exist`, or `cannot change return type of existing function`.

Read [SKILL.md](SKILL.md) for the guard patterns. This file is when to reach
for it and what the guards look like.

## Using it

It fires before writing or reviewing any migration that touches a Supabase
namespace, and on any of:

- "fix the CI migration job" / "migration failed in CI"
- "vanilla postgres errored on this migration"
- "schema auth does not exist"
- a diff in `supabase/migrations/*.sql` referencing `auth.`, `storage.`,
  `realtime.`, or a `create or replace function` whose signature moved

It deliberately does **not** fire when the migration only touches the `public`
schema with no Supabase-namespace references — there is nothing to guard.

## Example

The core move: leave the column unconstrained, bind the FK conditionally.

```sql
create table upload_jobs (
  id          uuid primary key default gen_random_uuid(),
  uploader_id uuid,                        -- unconstrained in vanilla CI
  ...
);

do $$ begin
  if to_regnamespace('auth') is not null
     and to_regclass('auth.users') is not null then
    execute 'alter table upload_jobs
               add constraint upload_jobs_uploader_id_fkey
               foreign key (uploader_id) references auth.users(id)
               on delete set null';
  end if;
end $$;
```

Vanilla CI applies the table and skips the FK; Supabase environments get the
real constraint. The same `to_regnamespace` probe wraps policies calling
`auth.uid()`. Note the order — probing `to_regclass('auth.users')` alone panics
when the whole schema is missing, so the namespace check comes first.

A two-line header comment explains *why* the column is unconstrained;
otherwise a future maintainer "helpfully" tightens it and breaks CI again. And
before pushing, the whole chain is smoke-tested locally against a Postgres
container whose image tag and bootstrapped roles are read from the CI workflow
itself — about 30 seconds.

## Related

- `probe-migration-in-transaction` (this plugin) — this skill gets the
  migration to *apply* everywhere; that one proves what it *does*.
- `prove-the-check-can-fail` (verification plugin) — the local smoke-test is
  only trustworthy because it mirrors CI exactly; same discipline of running
  the real check, not a lookalike.
