---
name: pre-publication-sweep
description: >
  Use before a repository or its content crosses the line it cannot come back
  from — flipping private to public, publishing an extract, pushing to a host
  others can read. Fires on "make it public", "open source this", "check
  nothing confidential leaks". Do NOT fire on a repo that is already public —
  its history is already out, and the task is exposure response, not a sweep —
  or for content that never leaves the machine.
---

# Pre-publication sweep

Publishing is a write with no undo: caches, forks and mirrors outlive a
deletion. The deliverable is the list of commands run and their empty result —
never the word "clean" on its own — or the verbatim hits, handed to the owner.

## Procedure

1. **Build the term list from the people involved, not from imagination**:
   personal email addresses, employer and internal project names, machine
   hostnames, credential prefixes (`sk-`, `ghp_`, `AKIA`). Ask the owner what
   is sensitive — you cannot grep for a name you were never told, and a sweep
   against a guessed list reports a confident false clean.

2. **Sweep the working tree**: `grep -rIiE '<terms>' . --exclude-dir=.git`,
   adding `--exclude-dir` for any vendored tree you will sweep as its own repo.

3. **Sweep every blob in every commit on every branch** — a file deleted years
   ago still publishes with the history:

   ```bash
   git rev-list --all --remotes | while read -r c; do
     git grep -iIlE '<terms>' "$c"
   done | sort -u
   ```

4. **Sweep commit metadata** — messages carry names, and author/committer
   emails publish through `.patch` URLs and the API:
   `git log --all --format='%ae %ce %s' | grep -iE '<terms>'`.

5. **Re-verify on the remote, never only a local clone.** The remote is what
   gets published, and a clone can be stale in either direction — including
   showing clean where the remote is not:

   ```bash
   gh api 'repos/<owner>/<repo>/commits?sha=<branch>&per_page=100' \
     --jq '.[].commit | .author.email, .committer.email' | sort -u
   ```

   Run it per branch — enumerate them with
   `gh api 'repos/<owner>/<repo>/branches' --jq '.[].name'` — and add
   `--paginate` when a branch holds more than 100 commits, or the tail of the
   history silently escapes the sweep.

6. **Run the repo's secret scanner** (gitleaks, or whatever the repo already
   enforces) — entropy and token patterns catch what a name list cannot.

7. **Report commands plus results.** An empty sweep is evidence only when the
   reader can see what was swept.

## When to STOP

- **Any hit** — stop and report it verbatim. Scrubbing is the owner's
  decision, not yours: it may require a history rewrite, which orphans every
  pin on the old SHAs and has its own fallout.
- **The repo is already public** — a sweep is theatre; the question is what
  was exposed and for how long.
- **You cannot enumerate the sensitive terms** — ask the owner rather than
  guessing. The false clean is worse than the delay.
