# data-safety

Writes that are hard to undo — four skills for the operations where "oops"
is a rollback plan written too late, or not at all.

```bash
claude plugin install data-safety@hard-won-skills --yes
```

The common thread is irreversibility. A migration's real behaviour only shows
up under the roles that will meet it; a bulk write is judged by what you can
undo, not what you intended; a published git history outlives every deletion
through caches, forks and mirrors. Each skill here makes the irreversible step
observable *before* it happens — in a transaction that rolls back, behind an
invariant measured first, or in a sweep whose empty result is shown rather
than asserted.

## The skills

| Skill | What it does |
|---|---|
| [`probe-migration-in-transaction`](skills/probe-migration-in-transaction/README.md) | Apply the migration inside `begin`…`rollback`, interrogate it as each role, and deliver a role × capability matrix — leaving nothing behind |
| [`reversible-bulk-write`](skills/reversible-bulk-write/README.md) | Name the invariant, dry-run every stage, write the rollback before applying, report before-and-after numbers |
| [`supabase-ci-migration-guards`](skills/supabase-ci-migration-guards/README.md) | Guard the Supabase-managed-schema references that pass review and then fail on vanilla-Postgres CI |
| [`pre-publication-sweep`](skills/pre-publication-sweep/README.md) | Before anything goes public: sweep the working tree, every blob in history, commit metadata and the remote — and report commands plus results, never just "clean" |

Each skill's README carries its triggers and a worked example; the `SKILL.md`
beside it is the procedure the agent follows.
