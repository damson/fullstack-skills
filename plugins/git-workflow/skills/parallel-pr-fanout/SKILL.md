---
name: parallel-pr-fanout
description: >
  Use when a batch of 3+ independent changes should land as SEPARATE pull
  requests built by parallel agents — "address all of these", "fix everything
  on the list", "make as much parallel work as possible", a review or audit
  producing many unrelated fixes. Goal — reviewable, file-disjoint PRs that
  merge in any order. NOT for coupled changes (one PR), sequential work
  (a stack), or generic non-PR parallelism (that is plain agent dispatch).
---

# Parallel PR fan-out

Running N agents is the easy part. The batch succeeds or fails on two things
decided *before* launch: whether any two agents can touch the same file, and
whether each agent's brief carries the facts it cannot discover. Get the first
wrong and the PRs conflict on arrival; get the second wrong and a confident
agent ships a plausible fix to the wrong problem.

## Procedure

1. **Partition by file ownership, not by topic.** List every file each unit
   will touch — including the ones topics forget: the shared test file, the
   docs table that indexes scripts, the README section a change falsifies, the
   `.gitignore`. Two units sharing any file merge into one unit or run in
   sequence. State each agent's allowed file set explicitly and name the files
   it must NOT touch as "owned by parallel agents".

2. **Write the brief an agent cannot reconstruct.** Findings with `file:line`,
   what was already ruled out, the repo's invariants that apply, and the exact
   verification commands. An agent without these ranks confidently wrong — and
   reads just as authoritative either way.

3. **Standard boilerplate, verbatim in every brief:**
   - branch from `origin/<integration branch>`, never the local one;
   - run the repo's full verification (tests, linters) before pushing;
   - commit hygiene the repo enforces (no AI signatures where banned, subject
     style, one focused commit);
   - PR body from the repo's template, ticking only what the agent verified,
     CI left unticked at open;
   - never merge, never push protected branches;
   - findings OUTSIDE the allowed file set go in the PR body as flagged
     follow-ups, never as fixes — the scope fence is what makes the batch
     mergeable.

4. **Isolate per agent** — one worktree each; the primary checkout stays
   untouched. Never let an agent run machine-mutating installers (setup
   scripts, global linkers) from its worktree.

5. **Collect by notification, not polling.** As each agent reports, verify its
   PR exists and hand the CI question to `await-pr-checks` (or its
   discipline, where that skill is absent: pinned SHA, named checks, empties
   are pending).

6. **Report one row per PR** — number, one-line intent, CI state — plus
   anything an agent flagged out of scope. The user merges; order should not
   matter, because step 1 made it not matter.

## When to STOP

- **Two partition attempts still share a file.** The work is coupled; propose
  one PR or an explicit sequence instead of forcing the split.
- **A unit needs a user decision mid-flight** (API choice, naming, scope) —
  pull it out of the batch rather than letting an agent guess.
- **The batch exceeds what the user can review** (~8 PRs) — confirm the scale
  before launching; a fan-out nobody reviews is a queue, not a speed-up.
- **Units are independent but share machine state** (ports, global config,
  caches) — worktrees do not isolate that; sequence those units.
