---
name: android-verify-on-device
description: >
  Use when a UI or behaviour change has to be confirmed on a running Android app
  rather than by a test — a setting that must take effect, a screen that has never
  been opened, a class the project cannot construct under Robolectric. Fire when the
  user says "check it on the device", "does it actually work", "run it and look", or
  when a change lands in a class that reaches Play Services and so has no unit-test
  seam. Fire also when a layout question has been answered twice from captures and the
  answer keeps moving, or when what is on screen depends on something a test cannot
  supply: a filled ad, a real inset, an orientation the manifest may lock away. Skip
  when a screenshot golden or a Robolectric test can hold the same claim — they are
  cheaper and they run in CI, which this never does.
---

# Verify a change on a device

Driving an emulator is slow and every step of it can lie. A tap can miss and be
silently absorbed by the app; a capture can be of the previous screen, of a
transition, or of a splash frame that has not been replaced yet. **Each of those
reads as "the change did not work".** The cost of getting it wrong is not a failed
check, it is a real fix reported as broken and then "fixed" again.

So never act on a capture without knowing which activity was resumed and that the
frame changed since the action.

## Procedure

1. **Install the build you mean to test.** `./gradlew :app:installDebug` after the
   change compiles. Where the state under test is stored, `adb uninstall` first —
   a preference left by an earlier run is the most common false result.

2. **Launch and wait for a real frame**, not for the command to return:

   ```bash
   adb shell am force-stop <pkg>
   adb logcat -c                       # BEFORE the launch, or see below
   adb shell monkey -p <pkg> 1 >/dev/null 2>&1
   until adb logcat -d | grep -q "Displayed <pkg>/.*MainActivity"; do sleep 1; done
   ```

   **Clear the buffer first, or the wait is not a wait.** `logcat -d` dumps the
   whole ring buffer, so the `Displayed` line from a launch ten minutes ago matches
   on the first pass and the loop returns before this launch has drawn anything —
   green, instant, and wrong. If the buffer cannot be cleared, match on a line
   newer than a timestamp you took first (`adb logcat -d -t "$ts"`).

   `am start` cannot reach an activity declared `android:exported="false"` — reach
   those through the app's own UI, not through adb.

3. **Locate controls, never guess coordinates.**

   ```bash
   adb shell uiautomator dump /sdcard/ui.xml
   adb shell cat /sdcard/ui.xml | tr '>' '\n' | grep 'content-desc="Settings"'
   ```

   Read `bounds="[l,t][r,b]"` and tap its centre. A guessed tap that misses does not
   fail — on a drawing canvas it draws a stroke, on a list it scrolls, and either way
   the next screenshot shows a screen you did not intend and no error anywhere.
   `uiautomator` also proves the control is *present*, which a screenshot of a
   collapsed drawer does not.

4. **Capture against the frame from before the action**, not against the last one.
   Equality is the right stop condition but the wrong start: a launch splash and the
   held first frame of an animation are both already equal to themselves, so a loop
   that waits only for stillness returns before anything has happened. Wait for the
   frame to change first, then for it to stop changing.

   ```bash
   grab() { adb shell screencap -p /sdcard/n.png >/dev/null; adb pull /sdcard/n.png "$1" >/dev/null; }

   grab before.png                        # BEFORE the tap
   adb shell input tap "$x" "$y"
   until grab now.png && ! cmp -s now.png before.png; do sleep 1; done   # something moved
   until grab b.png && cmp -s b.png now.png; do cp b.png now.png; sleep 1; done  # and stopped
   ```

   The first loop rules out a stale frame, the second rules out a mid-animation one.
   Neither is optional, and `dumpsys` reporting the new activity resumed does **not**
   mean its surface has been drawn.

5. **Confirm what you are looking at** before reading anything off it:

   ```bash
   adb shell dumpsys activity activities | grep topResumedActivity
   ```

   Not the activity you expected means the tap missed, not that the feature is
   broken: go back to step 3 and re-read the bounds, because the screen has moved
   under you. Report a feature broken only from a frame you have confirmed is its own.

6. **Crop 1:1 before claiming anything about a small element.** A downscaled
   full-screen capture invents detail — a duplicated handle, an icon that is not
   there. Derive the box from the `bounds="[l,t][r,b]"` step 3 already parsed,
   padded by roughly half the control's size so its surroundings are visible:

   ```bash
   # bounds [928,2125][1023,2220] -> pad 48
   python3 -c "from PIL import Image; Image.open('now.png').crop((880,2077,1071,2268)).save('crop.png')"
   ```

   Pillow is the assumption; `sips -c` or ImageMagick `convert -crop` do the same job.
   Look at the crop. A dimension or a file size is not evidence of what is in it.

7. **Prefer the store to the pixels** where the claim is about state. Reading the
   value the app actually persisted settles in one command what a screenshot argues
   about:

   ```bash
   adb shell run-as <pkg> cat /data/data/<pkg>/shared_prefs/<name>.xml
   ```

   `run-as` works only on a debuggable build. "package not debuggable" means the
   build, not the state: reinstall the debug variant (step 1) and re-drive — or,
   where reinstalling would wipe the very state under test, fall back to reading
   the outcome off a confirmed frame (steps 3–6).

8. **Restore what you changed.** Emulator-wide settings outlive the run:
   `adb shell cmd uimode night auto`, and any
   `cmd overlay enable com.android.internal.display.cutout.emulation.*`. Delete files
   pushed to `/sdcard`.

## Before trusting a capture instead

A golden is cheaper than this page and usually right, so the question is not which is
better but what the capture cannot contain. Three things it cannot, each of which reads
as a finished screen rather than a missing one:

- **A view with nothing to show measures 0x0.** An unfilled ad, an image that has not
  decoded. Stacked in a column nobody notices; beside one, the column collapses and takes
  the panel's width with it. The capture is not wrong, it is of a different layout.
- **A configuration the app cannot reach.** A landscape golden of an activity locked to
  portrait reads exactly like one a user could see. Check the manifest before measuring
  anything off an orientation.
- **A preview that pins what the component would have decided.** Passing a parameter the
  component defaults from the window means every capture shows one branch — usually the
  branch the preview exists to disprove.

When a capture has answered the same layout question twice and the answer keeps changing,
stop reading captures. One run on a device settles it.

## Report only what you saw

Name the build, the device and its API level, and what you drove. Where a step could
not be driven, say so — an unstated gap reads as coverage.

## When to STOP and ask

- **The behaviour can be held by a test.** Stop and write the test; it runs in CI and
  this does not. Hand-driving is for arrangements the project genuinely cannot
  construct — a View reaching an ad SDK, a manifest-declared activity, a real inset.
- **Three navigation attempts have failed.** The app is not the problem; the driving
  is. Switch to `uiautomator` bounds if you were guessing, and if that fails, say the
  path could not be driven rather than reporting the feature broken.
- **The result contradicts a passing test.** Suspect the capture before the code, and
  re-read step 4.
- **A destructive step is needed** — wiping app data, uninstalling something the user
  did not install, changing a device-wide setting you cannot restore.
