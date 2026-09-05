# mutation-proof-harness

Runs the break-it-and-watch-it-go-red loop over several guards at once, and
refuses to count a result it cannot trust. Hand-driving that loop produces two
failure modes that both look like success: a test filter that selects nothing
exits 0, and a mutation that edits the file without changing behaviour still
passes. Both are silent, so the tally reads the same either way.

Read [SKILL.md](SKILL.md) for the procedure. This file is what a run looks like
and when to reach for it.

## Using it

Reach for it when more than one guard needs proving and a script is about to be
written by hand:

- "prove the checks can fail"
- "watch them go red"
- a PR test plan is about to claim several new guards were proved
- a batch of assertions, lint rules or CI steps landed together and none has
  ever been seen failing

It does **not** decide whether a guard is worth proving, and it is overkill for
a single ad-hoc mutation: `prove-the-check-can-fail`, in this same plugin, owns
both of those.

## Example

Nine new assertions land in one PR. Proving them one at a time is where the
silent passes hide.

1. **Commit first.** `git checkout -- <file>` restores from the *index*, not
   from HEAD, so staged-but-uncommitted work survives the restore and stays
   staged, and the clean-tree check at the end then reads as a failed restore
   when nothing failed.
2. **Define two things** and write everything else against them: one command
   that runs the suite filtered to a single test name, and the list of names.
3. **Prove the baseline before mutating anything.** Every filter must come back
   green *and* non-empty. This is the half that gets skipped, and it is the one
   that matters: a filter selecting no tests exits 0, so every mutation after it
   is measured against nothing. The check greps the runner's own "nothing ran"
   wording, which differs per tool.
4. **Mutate, diff, run, restore** — with the diff printed every time.
   `git diff --quiet` catches only the total misses; the printed diff is what
   catches a mutation that changed the wrong line, which `--quiet` reports as a
   success. A `trap` restores the file if the run is interrupted, so a hang
   cannot leave a mutated guard behind with nothing pointing at it.
5. **Treat GREEN as unproven, not as a pass.** Suspect the mutation before the
   test, in this order: the edit was a no-op at runtime; an earlier early-return
   already handled the case; under `perl -0pi` only the first match was
   replaced and it hit the wrong branch; the filter's test never imports the
   file you mutated. Retarget, re-run, and report the retarget.
6. **Report the count and that the baseline ran** —
   `proved-able-to-fail: 8   not-proved: 1` — with `git status --short` clean,
   because every mutation was restored.

"Eight of nine went red first time" is what makes the ninth worth reading.

## Why it is shaped like this

- **The tally is the deliverable, and an untrustworthy tally is worse than
  none.** Both silent failure modes inflate it, which is precisely how a set of
  inert guards gets reported as proved.
- **It is a script, not a habit.** Nine guards driven by hand is where the
  baseline check gets skipped "just this once", and the skipped baseline is the
  failure that hides the other eight.
- **Perl expressions that quietly do nothing get their own section**, because
  each one cost a diagnostic round: `\Q…\E` does not stop interpolation, `/` as
  a delimiter fights paths and regexes, `-0pi` replaces once, and a
  double-quoted shell string adds an expansion layer whose escapes are per
  layer.

## Related

- `prove-the-check-can-fail`, in this plugin: it decides whether a guard is
  worth proving and owns the single-mutation case. This runs the loop when
  several need it at once.
- `diagnose-a-lying-signal`, for the outcome this skill is designed to surface:
  a green that reports work which never happened.
