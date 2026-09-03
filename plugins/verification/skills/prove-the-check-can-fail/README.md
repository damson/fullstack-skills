# prove-the-check-can-fail

Breaks the thing on purpose and watches the check go red before trusting the
green. A passing check only proves it ran; failing proves it was looking at the
right thing. And a check that cannot fail is worse than no check, because it
gets reported as coverage.

Read [SKILL.md](SKILL.md) for the procedure. This file is what a run looks like
and when to reach for it.

## Using it

Ask for it in any of these shapes; the skill fires on the intent, not on a
command:

- "does that actually test anything?"
- "is that really covered?"
- a check passes on its very first run, having never been seen red
- you are wiring a test, assertion, screenshot golden, lint rule or CI step and
  are about to report it as coverage

It deliberately does **not** fire for test-driven work: there the test was
already seen failing before the fix, which is the whole point of TDD; redoing
the experiment proves nothing new.

## Example

A CI step greps migrations for a `WITH CHECK` clause, and it is green. Is it
guarding anything?

1. **Name the defect.** "A policy that lets a row be written without the check
   its `USING` half promises."
2. **Introduce it**, smallest possible edit, backed up first:
   `cp policy.sql "$TMPDIR/orig"`, then delete the `WITH CHECK` clause. Never
   `git checkout <file>` to restore; that discards any uncommitted work the
   file already had.
3. **Run the check the way CI runs it.** Same task, same flags.
   - Still green → suspect the check is inert; rule out caching, a filter that
     never selected it, and a mutated file the run does not read before
     concluding. Once confirmed, that finding matters more than whatever you
     were doing.
   - Finished suspiciously fast → suspect caching (`--rerun-tasks`,
     `--no-cache`, a preceding `cargo clean`). A cached pass invalidates the
     experiment.
   - Red → confirm the failure message names *this* defect, not something else.
4. **Restore and re-run**: `cmp "$TMPDIR/orig" policy.sql`, `git status`, green
   again from the restored state.
5. **Report both halves**: "fails when broken, passes when fixed", failure
   message quoted.

The worked defect above is also the skill's subtlest trap: a rule stated twice
by design (a policy's `USING` and its `WITH CHECK`, a guard in both branches)
survives a presence assertion when either half is deleted. Assert the count,
then mutate each occurrence in turn: deleting ONE occurrence is the mutation
that exposes it.

## Why it is shaped like this

- **The still-green outcome is the payoff.** Screenshot tasks that compare no
  pixels, scans over an empty input set, generated artifacts that a setup step
  quietly rebuilds: each reports a perfect run while checking nothing. Only a
  deliberately introduced defect tells them apart from a real pass.
- **It stops rather than pretends.** Where breaking things is unsafe
  (production data, a live migration), the skill has you reason it through and
  say plainly that the check was not empirically falsified; never report a
  staged proof that did not happen.

## Related

- `verify-dependency-behaviour`, the complement: this skill asks "would my
  check catch the bug?", that one asks "does the library do what its name
  implies?".
- `data-safety:probe-migration-in-transaction` and
  `mobile-ui:android-screenshot-baseline-verify` both apply this discipline in
  their own domains (break the policy in a second transaction; perturb a
  composable and watch the golden fail).
