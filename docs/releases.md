# How this repo releases

Two long-lived branches. `develop` integrates; `main` is what people install.
`claude plugin marketplace add` clones the default branch, so a commit is
released the moment it reaches `main` — nothing else is required, and nothing
else can hold it back.

## The cadence

`.github/workflows/release.yml` runs daily and asks three questions. All three
must say yes, or it logs why it is holding and exits:

1. **Is `develop` ahead of `main`?** Nothing to release, no release.
2. **Is the newest tag at least three days old?** This is what makes the cadence
   three days. It is enforced in the job rather than in the cron expression
   because GitHub's schedule has no clean three-day form — `*/3` on day-of-month
   restarts every month, leaving a one-day gap after the 31st and a four-day one
   in February.
3. **Is there no release PR already open?** If there is, it refreshes that one.

`workflow_dispatch` bypasses the three-day gate. It never bypasses the other two:
you cannot release nothing.

## What a release does

- Patch-bumps `plugin.json` for **only** the plugins with changes under
  `plugins/<name>/**`, and commits that to `develop`. Untouched plugins keep
  their version, so `claude plugin update` re-fetches only what moved.
- Opens the `develop → main` pull request with the inventory: which versions
  moved, which PRs are in the batch, the diffstat, the commits.
- Runs the CI suite and enables auto-merge.
- Once merged, tags `vYYYY.MM.DD` and publishes a GitHub Release. `main` is
  only tagged once it is a release point — while `develop` is ahead and no
  release has ever happened, `main` is a baseline and is left alone. Tagging
  it would publish a release containing none of the merged work, and the
  fresh tag would then hold the real first release behind the three-day gate.
- Fast-forwards `develop` back to `main`, so the branches do not drift.

Marketplace tags are CalVer and plugin versions are semver on purpose. The tag
answers *when*; a plugin's version answers *what changed in it*.

## Two couplings that will not announce themselves

**The required check is matched by name.** Branch protection on `main` requires
a context called `validate`, which is the job id in `ci.yml`. Rename the job and
protection silently stops gating anything — the release still merges, just
unchecked. They move together or not at all.

**The release PR must merge with a merge commit, never a squash.** The
back-merge fast-forwards `develop` to `main`, which only works while `develop`
is an ancestor of `main`. A squash is not the commits it squashed, so it breaks
that relationship and the next back-merge falls back to opening a PR.

## Holding a release

Close the release PR. The next run reopens one when the cadence comes round
again. To hold for longer, disable the workflow in the Actions tab — the gates
have no "paused" state, deliberately, because a paused release is one nobody
remembers to resume.

## The tests, and where they came from

`scripts/validate-skills.sh` is vendored from `agent-config-harness`, at the
commit named in its header. It is a copy rather than a submodule because that
repo is private and this one is headed for public: fork pull requests receive no
secrets, so a private submodule would mean no outside contributor could ever get
a green check.

When `agent-config-harness` is public, migrating back is one line in `ci.yml`
and deleting the vendored copy. Until then, `diff` the two files when the
harness moves.

`scripts/validate-marketplace.py` has no upstream. It checks the wiring the
harness knows nothing about: that `marketplace.json` lists every plugin
directory and no phantom ones, that each `plugin.json` name matches its folder
and carries a semver version, and that the README's per-plugin skill counts and
skill lists still match the tree.
