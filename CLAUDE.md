# CLAUDE.md — fullstack-skills

Read [README.md](README.md) first — what this marketplace is, the themes, and
the two validators. Releases: [docs/releases.md](docs/releases.md). The
directives below are agent-only.

## Before committing

- Run both checks CI runs: `./scripts/validate-skills.sh` and
  `python3 scripts/validate-marketplace.py`.
- A skill added, removed or materially changed updates the README theme table
  and skill list, and minor-bumps its plugin's version, **in the same PR**. The
  release workflow adds the patch bump; never pre-apply it.
- In a plugin's README section, any backticked lowercase word is read as a
  skill name by `validate-marketplace.py` — keep prose there backtick-free.

## Branches and merges

- Feature branches cut from `origin/develop`; feature PRs squash-merge into
  `develop`.
- The release PR (`develop → main`) merges with a **merge commit, never a
  squash** — why, and what a squash costs: `docs/releases.md`.

## Cross-skill references

A skill may cite a skill from another plugin by name ("same discipline as
`prove-the-check-can-fail`") but must read correctly when that plugin is not
installed — a soft reference, never a hard dependency.
