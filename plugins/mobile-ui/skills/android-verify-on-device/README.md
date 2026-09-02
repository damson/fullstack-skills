# android-verify-on-device

Drives a real device or emulator to confirm a change no test can hold — and
protects the verdict from every way the driving itself can lie. A tap that
misses is silently absorbed; a capture can show the previous screen, a
mid-animation frame, or a splash that has not been replaced. Each reads as
"the change did not work", and the cost is a real fix reported as broken and
then "fixed" again.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it looks like in
use and how to reach it.

## Using it

Ask in any of these shapes:

- "check it on the device"
- "does it actually work"
- "run it and look"
- a change lands in a class with no unit-test seam (reaches Play Services, an
  ad SDK, a real inset)
- a layout question has been answered twice from captures and the answer keeps
  moving

It deliberately does **not** fire when a screenshot golden or a Robolectric
test can hold the same claim — they are cheaper and they run in CI, which this
never does. The skill's own first STOP rule is "the behaviour can be held by a
test: go write the test".

## When a golden is not enough

The skill names three things a capture cannot contain, each of which reads as a
finished screen rather than a missing one:

- **A view with nothing to show measures 0x0** — an unfilled ad, an undecoded
  image. The capture is not wrong; it is of a different layout.
- **A configuration the app cannot reach** — a landscape golden of an activity
  locked to portrait reads exactly like one a user could see.
- **A preview that pins what the component would have decided** — every capture
  shows one branch, usually the branch the preview exists to disprove.

## Example

Confirming a settings toggle actually persists and re-renders:

1. **Install the build you mean to test**; `adb uninstall` first where stored
   state is the thing under test — a leftover preference is the most common
   false result.
2. **Launch and wait for a real frame** — clear logcat *before* launching, or
   the `Displayed` line from ten minutes ago satisfies the wait instantly:
   green, instant, and wrong.
3. **Locate the control with `uiautomator dump`**, tap the centre of its
   `bounds` — a guessed tap that misses draws, scrolls, or navigates, with no
   error anywhere.
4. **Capture against the frame from before the tap** — wait for the screen to
   change, *then* for it to stop changing. A splash frame is already equal to
   itself; stillness alone is the wrong stop condition.
5. **Confirm the resumed activity** (`dumpsys activity activities`) before
   reading anything off the capture — the wrong activity means the tap missed,
   not that the feature is broken.
6. **Prefer the store to the pixels** for state claims:
   `adb shell run-as <pkg> cat …/shared_prefs/<name>.xml` settles in one
   command what a screenshot argues about.
7. **Restore what you changed** — device-wide settings outlive the run.

The report names the build, the device and API level, and what was driven;
an unstated gap reads as coverage.

## Related

- [`android-screenshot-baseline-verify`](../android-screenshot-baseline-verify/README.md) —
  the cheaper check, when a golden *can* hold the claim.
- [`android-screenshot-baseline-record`](../android-screenshot-baseline-record/README.md) —
  recording the golden that makes this skill unnecessary next time.
