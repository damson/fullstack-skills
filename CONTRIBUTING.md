# Contributing

Thanks for being here — issues and pull requests are both welcome, and small
counts: a skill that stopped matching its tool's current behaviour is a bug
worth [reporting](https://github.com/damson/fullstack-skills/issues/new) even
without a fix, and a worked example that makes a skill's README clearer is a
real contribution.

The full guide lives in the
[README's Contributing section](README.md#-contributing). The short version:

## The bar for a new skill

Every skill here was extracted from a real session where not having it cost
something. A new one meets the same bar: it encodes something that **actually
went wrong and would go wrong again** — not something that might. It ships as
two files: a `SKILL.md` with a `## Procedure` and a `## When to STOP` section,
and a `README.md` with its triggers and a worked example. Portable by default —
no paths from the repo it came from, graceful degradation where tooling may be
missing.

## Before you push

```bash
./scripts/validate-skills.sh              # structure of every skill
python3 scripts/validate-marketplace.py   # manifests and README vs the tree
```

Same two checks CI runs — no token, no network. Then three conventions the
validators cannot see:

1. Start the PR description from
   [the template](.github/PULL_REQUEST_TEMPLATE.md), never free-hand.
2. A skill added, removed or materially changed updates the root README's
   table and list, and minor-bumps its plugin's version, in the same PR.
3. Working here with an agent? Its rules live in [CLAUDE.md](CLAUDE.md).

PRs target `develop`; `main` is what people install, and a release workflow
promotes one to the other on its own cadence
([how releases work](docs/releases.md)).
