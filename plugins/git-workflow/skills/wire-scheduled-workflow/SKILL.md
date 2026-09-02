---
name: wire-scheduled-workflow
description: >
  Use when adding, renaming or debugging a GitHub Actions workflow that carries a
  `schedule:` or `workflow_dispatch:` trigger — especially in a gitflow repo where
  workflows land on `develop` first. Fire on "the cron never fired", "the
  workflow doesn't show up", "dispatch says workflow not found on the default
  branch", HTTP 404 from `gh workflow run`, or a review of a diff that adds
  either trigger. Skip for workflows with only `push` / `pull_request` triggers —
  those run from the pushed ref and have no registration step.
---

# Wire a scheduled workflow so it actually runs

GitHub registers `schedule` and `workflow_dispatch` only from the copy of the
workflow on the **default branch**. A workflow merged to `develop` in a gitflow
repo is not registered at all: the cron never fires, `gh workflow list` does not
show it, and a dispatch answers `404: workflow not found on the default branch`.
Nothing errors — two cron windows can pass before anyone notices. The same
applies to a **rename**: the new filename is a new, unregistered workflow until
it reaches the default branch.

## Procedure

1. **Name the triggers.** `grep -A5 '^on:' <workflow>`. Only `schedule` and
   `workflow_dispatch` need registration; `push` / `pull_request` run from the
   ref that raised the event and work from any branch.

2. **Check registration, don't assume it:**

   ```bash
   gh workflow list --all          # registered workflows, from the default branch
   gh workflow run <file>.yml      # a 404 here IS the diagnosis
   ```

3. **Trace the path to the default branch.** In a gitflow repo that is the next
   release. Two traps on the way:

   - **The workflow gates its own promotion.** A release workflow that lives
     only on `develop` cannot run to promote itself to `main` — putting it
     there *is* a release. The first promotion must be done by hand: replicate
     what the workflow's proposal step would have done, open the PR, merge it.
     Every run after that is automatic.
   - **A long-lived PR is not a path.** The workflow registers when the file
     lands on the default branch, not when the PR opens.

4. **After it lands, verify registration and the first firing:**

   ```bash
   gh workflow list --all                        # now it appears
   gh workflow run <file>.yml && gh run list --workflow=<file>.yml --limit 1
   ```

   A dispatch that starts a run is the proof. For the cron itself, check the
   run list after the first window passes — and know that a workflow whose
   *only* value was the schedule has still never had its steps exercised until
   then; a `workflow_dispatch` trigger alongside the cron exists precisely so
   the steps can be proven before the window.

5. **Write the trap down where the next rename will find it** — a comment at
   the top of the workflow or a line in the repo's release doc. The rename
   variant re-bites repos that survived the first variant.

## Sharp edges

- **The schedule runs the default branch's copy.** Editing the workflow on a
  feature branch changes nothing about what the cron executes until the edit
  merges through to the default branch.
- **`schedule` is disabled after 60 days without repo activity**, silently, and
  a maintainer has to re-enable it in the Actions tab. A cron that stopped in a
  quiet repo is usually this, not a syntax error.
- **Auto-merges performed with `GITHUB_TOKEN` raise no `push` event** for other
  workflows, so a push-triggered job cannot be the only path to something that
  matters — pair it with the schedule as the guaranteed path.

## When to STOP

- **The workflow needs secrets or permissions you cannot see** — registration
  is checkable from outside, the run's success is not; hand the verification to
  someone who can read the run logs.
- **The manual bootstrap would itself be a release** (as in the self-gating
  case) and the repo has release discipline — follow the repo's release
  procedure for that one promotion rather than pushing the file to the default
  branch directly.
- **The cron fired but the job did the wrong thing** — that is the workflow's
  logic, not its wiring; debug it as code, not as registration.
