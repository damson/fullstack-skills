# fullstack-skills

A Claude Code marketplace of skills, grouped by theme so you install only what
you actually work in.

```bash
claude plugin marketplace add damson/fullstack-skills
claude plugin install git-workflow@fullstack-skills --yes
```

Both commands are idempotent and exit `0` on a re-run. `--yes` is required when
stdout is not a TTY.

## The themes

| Plugin | Skills | What it is for |
|---|---|---|
| **git-workflow** | 8 | Branch, worktree and pull-request hygiene |
| **agent-config** | 8 | Writing and auditing agent instruction files |
| **verification** | 2 | Proving a check can fail before trusting it |
| **data-safety** | 3 | Writes that are hard to undo |
| **mobile-ui** | 3 | Android / Compose screenshots and Figma components |

### git-workflow

Rebase open PRs onto a base that has just merged, reply to review findings one
row per finding, prune dead branches and worktrees, embed a screenshot that
renders for reviewers on a private repo, report coverage as one sticky comment
with a threshold band rather than a fresh number every push, and check a diagram
still matches the system before ticking "architecture updated".

`branch-hygiene` · `pr-comment-loop` · `rewrite-pr-history` · `worktree-bootstrap` ·
`capture-pr-screenshots` · `github-pr-screenshot-embed` · `audit-diagram-claims` ·
`coverage-pr-comment`

### agent-config

Audit a `CLAUDE.md` stack for contradictions and duplication, keep a config file
a pointer rather than a copy of its sibling, notice when a repeated instruction
should become a skill, validate a skill against a real project before trusting
it, and capture a long session's learnings before compacting.

`agent-config-audit` · `claude-md-pointer-check` · `redundancy-check-before-ship` ·
`skill-opportunity-finder` · `validate-skill-against-real-project` · `prompt-coach` ·
`save-before-compact` · `session-retro`

### verification

Two skills for the same failure: believing a check that has never been observed
failing. One makes you break the thing on purpose and watch the check go red;
the other makes you run a dependency and observe its behaviour instead of
asserting what its naming implies.

`prove-the-check-can-fail` · `verify-dependency-behaviour`

### data-safety

Probe a migration inside a transaction and roll it back, interrogating it as
each role that will meet it. Make a bulk write reversible before running it.
Catch the Supabase-managed-schema traps that pass review and fail in production.

`probe-migration-in-transaction` · `reversible-bulk-write` · `supabase-ci-migration-guards`

### mobile-ui

Record and verify Compose screenshot baselines, including the silent no-op where
the task reports `PASSED` while comparing no pixels at all. Build a Compose
component from a Figma node, bound to design tokens rather than raw values.

`android-screenshot-baseline-record` · `android-screenshot-baseline-verify` ·
`figma-to-compose-component`

## What a skill here looks like

Every skill carries frontmatter whose `name` matches its folder, a `## Procedure`
(or `## Step N`) section, and a **`## When to STOP`** section. That last one is
the part most skill collections leave out, and it is what stops a skill firing on
a task it should decline.

Skills are written to be **portable**: none names a path from the repo it came
from, or assumes a folder layout. Where one can take advantage of tooling you may
not have, it says so and degrades instead of failing.

## Related

The engine these were extracted from — a domain registry, an LLM rubric that
scores config quality, and a `bats` suite that enforces skill structure — lives
separately in `agent-config-harness`.

MIT licensed.
