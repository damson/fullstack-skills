# android-screenshot-baseline-verify

Checks that existing screenshot baselines still pass, and that the run
**actually compared pixels**. The silent failure it guards: run the plain
unit-test task instead of the verify task and the capture calls become no-ops.
Tests pass, zero images are compared, and a refactor that changed every pixel
ships clean. Green is not the evidence; *comparisons performed* is.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it looks like in
use and how to reach it.

## Using it

Ask in any of these shapes:

- "run the screenshots"
- "do the baselines still pass"
- "check the goldens"
- "did my refactor change the rendered output?"
- before pushing after a theme, design-token or dependency change

It deliberately does **not** fire when:

- The project ships its own verification skill or documented incantation: use
  that; it knows the build's wiring.
- There are no baselines to check, or you mean to create/update them; that is
  `android-screenshot-baseline-record`'s job, and this skill sends
  "missing golden" runs there rather than treating them as failures.

## Example

Confirming a `:library:ui` refactor changed no pixels (Roborazzi):

1. **Find the verify task, not the test task**:
   `./gradlew :library:ui:tasks --all | grep -i roborazzi` →
   `verifyRoborazziDebug`. Running `testDebugUnitTest` instead executes the
   same test class and asserts nothing about pixels: the exact no-op this
   skill exists for.
2. **Confirm baselines exist**: count the PNGs first; zero means this is a
   recording job, not a verification one.
3. **Run the verify task**, scoped with `--tests` if you mean one class,
   a filter Roborazzi and Paparazzi take but AGP's validate task rejects.
4. **Confirm comparisons happened**: do not accept the exit code. Roborazzi
   writes `results-summary.json` with `total` / `unchanged` / `changed` /
   `added`; a non-zero `total` matching the tests you expect *is* the
   evidence. Three traps the skill defuses here: no diff artifacts on a green
   run is normal (diffs are written only on mismatch); the `-mmin` time bound
   is load-bearing because output directories accumulate stale images; and
   silencing `find` with `2>/dev/null` turns a parse error into "no evidence".
   If the tally cannot be established, the run **verified nothing**; report
   that, never "passing".
5. **Once per setup, prove it can fail**: perturb a padding, watch the task
   fail naming the image, revert, re-run to green. A verification never seen
   red is not yet a verification.
6. **Read the diff before deciding**: regression (fix the code), intended
   change (re-record via `android-screenshot-baseline-record`), or environment
   noise (do not re-record to make it pass; that hides the drift).

## Related

- [`android-screenshot-baseline-record`](../android-screenshot-baseline-record/README.md):
  creating or updating baselines; intended visual changes get re-recorded there.
- `prove-the-check-can-fail` (verification plugin): step 5 is that skill's
  discipline applied to pixels.
- [`android-verify-on-device`](../android-verify-on-device/README.md): for the
  claims no golden can hold at all.
