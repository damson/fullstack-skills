# CLAUDE.md — hard-won-skills

Read [README.md](README.md) first — what this marketplace is, the themes, and
the two validators. Releases: [docs/releases.md](docs/releases.md). The
directives below are agent-only.

## Before committing

- Run both checks CI runs: `./scripts/validate-skills.sh` and
  `python3 scripts/validate-marketplace.py`.
- A skill added, removed or materially changed updates the README theme table
  and skill list, and minor-bumps its plugin's version, **in the same PR**. The
  release workflow adds the patch bump; never pre-apply it.
- A `SKILL.md` edit checks the sibling `README.md` for claims it falsifies —
  the README narrates the procedure, and a changed step reads as documented
  behaviour until someone notices.
- In a plugin's README section, any backticked lowercase word is read as a
  skill name by `validate-marketplace.py` — keep prose there backtick-free.

## Branches and merges

- Feature branches cut from `origin/develop`; feature PRs squash-merge into
  `develop`.
- Merge a PR only after its CodeRabbit review is posted and answered, one row
  per finding. It auto-reviews PRs targeting `develop` (`.coderabbit.yaml`,
  read from the PR's **head** branch); `@coderabbitai review` triggers one
  manually. When its rate limit blocks a review, substitute an independent
  agent review on a cheap model (haiku), post that agent's findings as a PR
  comment, and answer them under the same gate — the review must still be
  independent of whoever wrote the diff.
- After a fix push, CodeRabbit often posts no new review object; its **check
  flipping to SUCCESS on the new head** is the signal that the push was
  reviewed. Read the check, not the reviews list, before retriggering, which
  spends quota to be told the commit was already reviewed.
- The release PR (`develop → main`) merges with a **merge commit, never a
  squash** — why, and what a squash costs: `docs/releases.md`.

## Cross-skill references

A skill may cite a skill from another plugin by name ("same discipline as
`prove-the-check-can-fail`") but must read correctly when that plugin is not
installed — a soft reference, never a hard dependency.
