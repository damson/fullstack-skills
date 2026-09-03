# Contributing

Thanks for being here — issues and pull requests are both welcome, and small
counts. A skill that stopped matching its tool's current behaviour is a bug
worth [reporting](https://github.com/damson/hard-won-skills/issues/new) even
without a fix. A worked example that makes a skill's README clearer is a real
contribution. So is a sharper trigger phrase, or a "When to STOP" case you hit
that a skill missed.

This file is the complete guide; the README carries only a summary of it.

## Ways to contribute

- **Report a stale skill.** Tools move. If a skill's command errors, its
  flag vanished, or its assumption no longer holds, open an issue quoting the
  line and what you observed instead — exit codes and output beat adjectives.
- **Improve a skill's documentation.** Each skill has a human-facing
  `README.md` beside its `SKILL.md`; clearer triggers and better worked
  examples are always in scope.
- **Sharpen a procedure.** Replace a judgment call with a runnable check,
  add the degrade path for tooling a stranger may not have, or add the
  STOP case you hit in the wild.
- **Add a skill.** The bar is below — read it before writing.

## The bar for a new skill

Every skill here was extracted from a real session where not having it cost
something — a check that could never fail, a release that could not tag
itself. A new skill meets the same bar: it encodes something that **actually
went wrong and would go wrong again**, not something that might. Measured
facts from the incident belong in the text; they are what make a rule
believable years later.

## What a skill ships as

Two files in `plugins/<theme>/skills/<skill-name>/`:

- **`SKILL.md`** — the procedure the agent follows:
  - frontmatter with a `name:` **matching the folder name exactly** and a
    `description:` that says when to fire *and when not to* — bad triggers
    spam, good triggers stay quiet;
  - a `## Procedure` (or `## Step N`) section;
  - a `## When to STOP` section — the cases where the skill hands back to the
    human instead of pressing on. This is enforced by the validator and is the
    difference between a procedure and a hazard.
- **`README.md`** — the human-facing half: what the skill produces and the
  failure it prevents, the phrases that reach it, one worked example grounded
  in the skill's own commands, and the sibling skills it relates to.

**Portability is non-negotiable**: no paths from the repo the skill came from,
no assumed folder layout, and where the skill can use tooling a stranger may
not have, it says so and degrades instead of failing. A reference to a skill
in another plugin must read correctly when that plugin is not installed — a
soft reference, never a hard dependency.

Skill names must be unique across the whole marketplace — skills install flat,
and duplicate leaf names would shadow each other.

## Before you push

Run the same two checks CI runs — no token, no network:

```bash
./scripts/validate-skills.sh              # structure of every skill
python3 scripts/validate-marketplace.py   # manifests, README, plugin pages and relative links vs the tree
```

Then the conventions the validators cannot see:

1. **Start the PR description from
   [the template](.github/PULL_REQUEST_TEMPLATE.md)**, never free-hand. Tick
   only what you actually verified — one aspirational tick makes every other
   tick unreliable.
2. **Bookkeeping travels with the change.** A skill added, removed or
   materially changed updates, in the same PR: the root README's theme table
   and skill list, the plugin folder's README table, and a **minor** bump of
   that plugin's version in `.claude-plugin/plugin.json`. The release workflow
   owns the patch field — never pre-apply it.
3. **If your change touches a check or a guard, prove it can fail** before
   trusting it — break the thing on purpose, watch it go red, restore. This
   repo ships a skill for exactly that discipline, and applies it to itself.
4. **Working with an agent?** The agent-facing rules for this repo live in
   [CLAUDE.md](CLAUDE.md).

## Branches and releases

Pull requests target **`develop`** — `main` is what people install, and a
workflow promotes develop to main on a three-day cadence when there is
something to release. Feature PRs squash-merge; the release PR merges with a
merge commit, enforced by a ruleset. Details, gates and how to hold a release:
[docs/releases.md](docs/releases.md).

## License

Contributions are accepted under the repository's [MIT license](LICENSE).
