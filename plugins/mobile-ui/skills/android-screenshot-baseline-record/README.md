# android-screenshot-baseline-record

Records screenshot-test baselines (golden images) in any Android/Compose
project (Roborazzi, Paparazzi, or AGP's Compose Preview Screenshot Testing)
and then **proves files were actually written**. A record run that writes
nothing still exits 0: the task was not wired to the module, the filter matched
zero tests, or the output went somewhere you were not looking. The build says
green either way; the evidence is in the baseline directory.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it looks like in
use and how to reach it.

## Using it

Ask in any of these shapes; the skill fires on the intent, not on a command:

- "record the baselines"
- "regenerate the screenshots"
- "update the snapshots"
- "the goldens are stale"
- staging a new `*ScreenshotTest.kt` with no images beside it

It deliberately does **not** fire when:

- The project ships its own recording skill or documented procedure; that one
  knows the build's wiring; this one avoids assuming any.
- You want to *check* existing baselines rather than create or update them;
  that is `android-screenshot-baseline-verify`'s job, and it hands back here
  only when a diff turns out to be an intended visual change.

## Example

Recording a first baseline for a new `BadgeScreenshotTest` in `:library:ui`:

1. **Identify the framework**: `grep` the build files; say it finds
   `io.github.takahirom.roborazzi`, so the record task is
   `recordRoborazzi<Variant>`. Confirm it exists for *this* module with
   `./gradlew :library:ui:tasks --all | grep -i roborazzi`; a task that does
   not appear is not wired there, and invoking it anyway is the quiet no-op
   this skill exists to catch.
2. **Count before recording**: locate the baseline directory and note the PNG
   count. Without a before-number, "it recorded" is unfalsifiable.
3. **Record scoped**: `:clean` first (stale intermediates get copied over
   fresh renders; `--rerun-tasks` does not clear them), then the record task
   with `--tests "…BadgeScreenshotTest*"`.
4. **Prove it wrote something**: `git status --short "$BASE"` is the command
   that matters, because it separates the three outcomes:
   - `??`: a new baseline was written (what we want here)
   - ` M`: an existing baseline changed
   - absent from the status: the golden was re-emitted byte-identical, which
     an mtime check would misreport as new
   No `??` and no ` M` after recording a test that had no baseline means the
   run recorded **nothing**, whatever the build said.
5. **Look at the images**: reject blank, unstyled (theme bypassed by a
   preview-only wrapper) or clipped captures. A wrong baseline is a contract
   for the wrong appearance, and every future run agrees with it.
6. **One commit** for the images and the test that produces them; split in
   two, CI runs the test against goldens that are not there yet.

## Related

- [`android-screenshot-baseline-verify`](../android-screenshot-baseline-verify/README.md):
  checking that existing baselines still pass; it sends "missing golden" cases here.
- [`figma-to-compose-component`](../figma-to-compose-component/README.md):
  hands off here after building a component, to prove the capture picked up the theme.
- `prove-the-check-can-fail` (verification plugin): the wider discipline behind
  never trusting a green you have not seen red.
