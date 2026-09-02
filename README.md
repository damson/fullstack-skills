# fullstack-skills

Skills for [Claude Code](https://claude.com/claude-code), distilled from real
working sessions — grouped by theme into five plugins so you install only what
you actually work in.

A skill is a procedure the agent loads when a task matches it: how to rebase a
stack of PRs without losing one, how to prove a screenshot test actually
compared pixels, how to probe a migration without leaving a trace. The ones
here share a lineage: **each was extracted from a session where the lack of it
cost something** — a check that could never fail, a release that could not tag
itself, forty-seven stale branches nobody could see. The measured facts stayed
in the text.

## Quick start

```bash
claude plugin marketplace add damson/fullstack-skills
claude plugin install git-workflow@fullstack-skills --yes
```

Both commands are idempotent and exit `0` on a re-run. `--yes` is required when
stdout is not a TTY. Repeat the install for any other theme in the table below;
`claude plugin update` re-fetches only plugins whose version moved.

You don't invoke a skill so much as walk into it: each one declares the
situations and phrases it fires on, and the agent picks it up when your task
matches — "rebase the open PRs", "do the baselines still pass", a push to a
branch with an open PR. Every skill also documents its triggers in a README
beside its procedure, so you can browse what you installed.

## The themes

| Plugin | Skills | What it is for |
|---|---|---|
| **git-workflow** | 10 | Branch, worktree and pull-request hygiene |
| **agent-config** | 8 | Writing and auditing agent instruction files |
| **verification** | 2 | Proving a check can fail before trusting it |
| **data-safety** | 4 | Writes that are hard to undo |
| **mobile-ui** | 4 | Android / Compose screenshots, Figma components, on-device checks |

### git-workflow

Rebase open PRs onto a base that has just merged, reply to review findings one
row per finding, prune dead branches and worktrees, embed a screenshot that
renders for reviewers on a private repo, report coverage as one sticky comment
with a threshold band rather than a fresh number every push, check a diagram
still matches the system before ticking "architecture updated", move a
vendored pin only with the evidence that earned the new commit, and wire a
scheduled workflow so its cron actually fires — GitHub registers schedule
triggers only from the default branch.

`branch-hygiene` · `pr-comment-loop` · `rewrite-pr-history` · `worktree-bootstrap` ·
`capture-pr-screenshots` · `github-pr-screenshot-embed` · `audit-diagram-claims` ·
`coverage-pr-comment` · `bump-vendored-pin` · `wire-scheduled-workflow`

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
Sweep a repository's full history and its remote before anything goes public.

`probe-migration-in-transaction` · `reversible-bulk-write` · `supabase-ci-migration-guards` ·
`pre-publication-sweep`

### mobile-ui

Record and verify Compose screenshot baselines, including the silent no-op where
the task reports `PASSED` while comparing no pixels at all. Build a Compose
component from a Figma node, bound to design tokens rather than raw values. And
where no test can hold the claim, drive the change on a real device without
trusting a stale frame or a tap that missed.

`android-screenshot-baseline-record` · `android-screenshot-baseline-verify` ·
`figma-to-compose-component` · `android-verify-on-device`

## What a skill here looks like

Every skill carries frontmatter whose `name` matches its folder, a `## Procedure`
(or `## Step N`) section, and a **`## When to STOP`** section. That last one is
the part most skill collections leave out, and it is what stops a skill firing on
a task it should decline — the difference between a procedure and a hazard.

Skills are written to be **portable**: none names a path from the repo it came
from, or assumes a folder layout. Where one can take advantage of tooling you may
not have, it says so and degrades instead of failing.

Beside every `SKILL.md` sits a `README.md` — the human-facing half: what the
skill produces, the phrases that reach it, a worked example, and the sibling
skills it hands off to. The `SKILL.md` stays the procedure the agent follows.

## Contributing

Issues and pull requests are welcome — a skill that stopped matching its tool's
current behaviour is a bug worth reporting even without a fix. The bar for a
new skill is the lineage above: it encodes something that actually went wrong
and would go wrong again, not something that might. Style and structure are
enforced mechanically:

```bash
./scripts/validate-skills.sh              # structure of every skill
python3 scripts/validate-marketplace.py   # manifests and README vs the tree
```

Those are the same two checks CI runs — no token, no network. Three conventions
the validators cannot see: start the PR description from
[the template](.github/PULL_REQUEST_TEMPLATE.md), never free-hand; a skill
added, removed or materially changed updates this README's table and list and
minor-bumps its plugin's version in the same PR; and agent-facing rules for
working in this repo live in [CLAUDE.md](CLAUDE.md).

## Releases

`develop` integrates, `main` is what `claude plugin marketplace add` installs.
A workflow promotes one to the other every three days, but only when there is
something to promote and the CI suite passes — plugins that changed get a patch
bump, the marketplace gets a CalVer tag. Gates, couplings and how to hold a
release: [docs/releases.md](docs/releases.md).

## Related

The engine these were extracted from — a domain registry, an LLM rubric that
scores config quality, and a `bats` suite that enforces skill structure — lives
separately in `agent-config-harness`.

[MIT licensed](LICENSE).
