# hard-won-skills

![Terminal-styled banner: a claude session announcing the hard-won-skills marketplace, over the tagline "Hard-won habits for Claude Code"](docs/assets/social-preview.png)

*Hard-won habits for [Claude Code](https://claude.com/claude-code), packaged so
you don't have to win them the hard way too.*

[![CI](https://github.com/damson/hard-won-skills/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/damson/hard-won-skills/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/damson/hard-won-skills?label=release&color=blue)](https://github.com/damson/hard-won-skills/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Coverage](https://codecov.io/gh/damson/hard-won-skills/branch/develop/graph/badge.svg)](https://codecov.io/gh/damson/hard-won-skills/branch/develop)
[![Made for Claude Code](https://img.shields.io/badge/made%20for-Claude%20Code-d97757.svg)](https://claude.com/claude-code)

👋 **Welcome!** This is a marketplace of **31 skills in 5 themed plugins**:
small, careful procedures your agent picks up automatically when a task calls
for them: rebasing a stack of PRs without losing one, proving a screenshot test
actually compared pixels, probing a migration without leaving a trace.

What holds them together is where they came from. **Every skill here was
extracted from a real session where not having it cost something**: a check
that could never fail, a release that could not tag itself, forty-seven stale
branches nobody could see. The measured facts stayed in the text, and so did
the scars: each skill knows not just what to do, but when to stop and ask.

**Jump to:**
[Quick start](#-quick-start) ·
[Pick your themes](#-pick-your-themes)
([git-workflow](#git-workflow) · [agent-config](#agent-config) ·
[verification](#verification) · [data-safety](#data-safety) ·
[mobile-ui](#mobile-ui)) ·
[What a skill looks like](#-what-a-skill-here-looks-like) ·
[Contributing](#-contributing) ·
[Releases](#-releases)

## 🚀 Quick start

Two commands and you're in:

```bash
claude plugin marketplace add damson/hard-won-skills
claude plugin install git-workflow@hard-won-skills --yes
```

Swap `git-workflow` for any plugin in [the table below](#-pick-your-themes),
and install as many as you like. Both commands are safe to re-run (idempotent, exit `0`), `--yes` is
only required when stdout is not a TTY, and `claude plugin update` re-fetches
just the plugins whose version moved.

**Then… do nothing.** You don't invoke a skill so much as walk into it: each
one declares the situations and phrases it fires on, and the agent picks it up
when your task matches: "rebase the open PRs", "do the baselines still pass",
a push to a branch with an open PR. Curious what you just installed? Every
skill has a README beside its procedure with its triggers and a worked
example; start with any link below.

## 🗂 Pick your themes

| Plugin | Skills | What it is for |
|---|---|---|
| **[git-workflow](plugins/git-workflow/README.md)** | 12 | Branch, worktree and pull-request hygiene |
| **[agent-config](plugins/agent-config/README.md)** | 8 | Writing and auditing agent instruction files |
| **[verification](plugins/verification/README.md)** | 2 | Proving a check can fail before trusting it |
| **[data-safety](plugins/data-safety/README.md)** | 5 | Writes that are hard to undo |
| **[mobile-ui](plugins/mobile-ui/README.md)** | 4 | Android / Compose screenshots, Figma components, on-device checks |

Not sure where to begin? **[verification](#verification)** is two skills,
takes a minute to read, and changes how you look at every green checkmark
you'll ever see again. (And if you only ever install one plugin, that's the
one we'd hand you.)

### git-workflow

Rebase open PRs onto a base that has just merged, reply to review findings one
row per finding, prune dead branches and worktrees, embed a screenshot that
renders for reviewers on a private repo, report coverage as one sticky comment
with a threshold band rather than a fresh number every push, check a diagram
still matches the system before ticking "architecture updated", move a
vendored pin only with the evidence that earned the new commit, and wire a
scheduled workflow so its cron actually fires (GitHub registers schedule
triggers only from the default branch). Two more from one long launch session:
wait out a PR's checks at a pinned SHA where an empty conclusion counts as
pending, and land a batch of independent fixes as file-disjoint PRs built by
parallel agents whose scope fences hold.

[`branch-hygiene`](plugins/git-workflow/skills/branch-hygiene/README.md) ·
[`pr-comment-loop`](plugins/git-workflow/skills/pr-comment-loop/README.md) ·
[`rewrite-pr-history`](plugins/git-workflow/skills/rewrite-pr-history/README.md) ·
[`worktree-bootstrap`](plugins/git-workflow/skills/worktree-bootstrap/README.md) ·
[`capture-pr-screenshots`](plugins/git-workflow/skills/capture-pr-screenshots/README.md) ·
[`github-pr-screenshot-embed`](plugins/git-workflow/skills/github-pr-screenshot-embed/README.md) ·
[`audit-diagram-claims`](plugins/git-workflow/skills/audit-diagram-claims/README.md) ·
[`coverage-pr-comment`](plugins/git-workflow/skills/coverage-pr-comment/README.md) ·
[`await-pr-checks`](plugins/git-workflow/skills/await-pr-checks/README.md) ·
[`parallel-pr-fanout`](plugins/git-workflow/skills/parallel-pr-fanout/README.md) ·
[`bump-vendored-pin`](plugins/git-workflow/skills/bump-vendored-pin/README.md) ·
[`wire-scheduled-workflow`](plugins/git-workflow/skills/wire-scheduled-workflow/README.md)

### agent-config

Audit a `CLAUDE.md` stack for contradictions and duplication, keep a config file
a pointer rather than a copy of its sibling, notice when a repeated instruction
should become a skill, validate a skill against a real project before trusting
it, and capture a long session's learnings before compacting.

[`agent-config-audit`](plugins/agent-config/skills/agent-config-audit/README.md) ·
[`claude-md-pointer-check`](plugins/agent-config/skills/claude-md-pointer-check/README.md) ·
[`redundancy-check-before-ship`](plugins/agent-config/skills/redundancy-check-before-ship/README.md) ·
[`skill-opportunity-finder`](plugins/agent-config/skills/skill-opportunity-finder/README.md) ·
[`validate-skill-against-real-project`](plugins/agent-config/skills/validate-skill-against-real-project/README.md) ·
[`prompt-coach`](plugins/agent-config/skills/prompt-coach/README.md) ·
[`save-before-compact`](plugins/agent-config/skills/save-before-compact/README.md) ·
[`session-retro`](plugins/agent-config/skills/session-retro/README.md)

### verification

Two skills for the same failure: believing a check that has never been observed
failing. One makes you break the thing on purpose and watch the check go red;
the other makes you run a dependency and observe its behaviour instead of
asserting what its naming implies.

[`prove-the-check-can-fail`](plugins/verification/skills/prove-the-check-can-fail/README.md) ·
[`verify-dependency-behaviour`](plugins/verification/skills/verify-dependency-behaviour/README.md)

### data-safety

Probe a migration inside a transaction and roll it back, interrogating it as
each role that will meet it. Answer data questions with a throwaway read-only
probe instead of a remembered number. Make a bulk write reversible before
running it.
Catch the Supabase-managed-schema traps that pass review and fail in production.
Sweep a repository's full history and its remote before anything goes public.

[`probe-migration-in-transaction`](plugins/data-safety/skills/probe-migration-in-transaction/README.md) ·
[`read-only-db-probe`](plugins/data-safety/skills/read-only-db-probe/README.md) ·
[`reversible-bulk-write`](plugins/data-safety/skills/reversible-bulk-write/README.md) ·
[`supabase-ci-migration-guards`](plugins/data-safety/skills/supabase-ci-migration-guards/README.md) ·
[`pre-publication-sweep`](plugins/data-safety/skills/pre-publication-sweep/README.md)

### mobile-ui

Record and verify Compose screenshot baselines, including the silent no-op where
the task reports `PASSED` while comparing no pixels at all. Build a Compose
component from a Figma node, bound to design tokens rather than raw values. And
where no test can hold the claim, drive the change on a real device without
trusting a stale frame or a tap that missed.

[`android-screenshot-baseline-record`](plugins/mobile-ui/skills/android-screenshot-baseline-record/README.md) ·
[`android-screenshot-baseline-verify`](plugins/mobile-ui/skills/android-screenshot-baseline-verify/README.md) ·
[`figma-to-compose-component`](plugins/mobile-ui/skills/figma-to-compose-component/README.md) ·
[`android-verify-on-device`](plugins/mobile-ui/skills/android-verify-on-device/README.md)

## 🧬 What a skill here looks like

Every skill is two files:

- **`SKILL.md`**, the procedure the agent follows: frontmatter whose `name`
  matches its folder, a `## Procedure`, and a **`## When to STOP`** section.
  That last one is the part most skill collections leave out, and it is what
  stops a skill firing on a task it should decline: the difference between a
  procedure and a hazard.
- **`README.md`**, the half written for you: what the skill produces, the
  phrases that reach it, a worked example, and the sibling skills it hands
  off to.

Skills are written to be **portable**: none names a path from the repo it came
from, or assumes a folder layout. Where one can take advantage of tooling you
may not have, it says so and degrades instead of failing.

## 🤝 Contributing

Found a rough edge? That's exactly the kind of thing this repo is made of: a
skill that stopped matching its tool's current behaviour is a bug worth
reporting even without a fix, and small contributions count: a clearer worked
example, a sharper trigger, a STOP case you hit in the wild. The bar for a
new skill is the lineage above: it encodes something that actually went wrong
and would go wrong again.

**[CONTRIBUTING.md](CONTRIBUTING.md) is the complete guide**: ways to
contribute, what a skill ships as, the two validators to run before pushing,
and the conventions they cannot see.

## 📦 Releases

`develop` integrates, `main` is what `claude plugin marketplace add` installs.
A workflow promotes one to the other every three days, but only when there is
something to promote and the CI suite passes: plugins that changed get a patch
bump, the marketplace gets a CalVer tag. Gates, couplings and how to hold a
release: [docs/releases.md](docs/releases.md).

## 🔗 Related

The engine these were extracted from (a domain registry, an LLM rubric that
scores config quality, and a `bats` suite that enforces skill structure) lives
separately in `agent-config-harness`.

[MIT licensed](LICENSE). Use them, fork them, make them yours.
