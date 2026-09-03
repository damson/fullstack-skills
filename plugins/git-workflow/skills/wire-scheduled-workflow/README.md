# wire-scheduled-workflow

Gets a scheduled GitHub Actions workflow actually running. GitHub registers
`schedule` and `workflow_dispatch` only from the copy of the workflow on the
**default branch** — a workflow merged to `develop` in a gitflow repo is not
registered at all: the cron never fires, `gh workflow list` does not show it,
and a dispatch answers `404: workflow not found on the default branch`.
Nothing errors, so cron windows pass unnoticed. The same trap re-bites on a
rename: the new filename is a new, unregistered workflow.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

Fires when adding, renaming or debugging a workflow with a `schedule:` or
`workflow_dispatch:` trigger — especially in a gitflow repo — or on:

- "the cron never fired"
- "the workflow doesn't show up"
- "dispatch says workflow not found on the default branch"
- an HTTP 404 from `gh workflow run`

It skips workflows with only `push` / `pull_request` triggers — those run from
the pushed ref and have no registration step.

## Example

A release workflow was merged to `develop` days ago and has never run. The
skill:

1. Names the triggers, then checks registration instead of assuming it:

   ```bash
   gh workflow list --all       # only default-branch workflows appear
   gh workflow run release.yml  # a 404 here IS the diagnosis
   ```

2. Traces the path to the default branch — the next release. Here it hits the
   sharpest variant: **the workflow gates its own promotion.** A release
   workflow living only on `develop` cannot run to promote itself to `main`,
   because putting it there *is* a release. The first promotion is done by
   hand — read the workflow's job steps, run the commands a run would have
   executed, open the PR it would have proposed, merge it — and every run
   after that is automatic.
3. Once the file lands, verifies registration and fires a dispatch, since a
   run that starts is the proof — the cron alone would leave the steps
   unexercised until its first window.
4. Writes the trap down where the next rename will find it — a comment at the
   top of the workflow, or a line in the release doc.

Three sharp edges worth knowing even without the skill: the schedule always
runs the default branch's *copy*, so feature-branch edits change nothing until
they merge through; `schedule` is silently disabled after 60 days of repo
inactivity; and auto-merges performed with `GITHUB_TOKEN` raise no `push`
event, so a push-triggered job cannot be the only path to something that
matters.

## Related

- `bump-vendored-pin` — pinned Action refs live in the same workflow files.
- `verification` plugin's `prove-the-check-can-fail` — the same "never seen it
  run ≠ wired" instinct, applied to checks instead of crons.
