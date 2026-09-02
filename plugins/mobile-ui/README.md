# mobile-ui

Android / Compose screenshots, Figma components and on-device checks — four
skills against the UI test that reports success while testing nothing.

```bash
claude plugin install mobile-ui@fullstack-skills --yes
```

Screenshot tooling has a signature failure: the run that compares no pixels
and exits 0. Run the plain unit-test task instead of the verify task and every
capture call becomes a no-op — tests pass, zero images compared, and a
refactor that changed every pixel ships clean. The same shape recurs when
recording baselines (a record run that wrote nothing still exits 0), when
rebuilding a Figma design the design system already had, and when a device
capture shows the previous screen instead of the result. These skills demand
the evidence: files written, comparisons counted, frames confirmed.

All four defer to a project-shipped skill when one exists — a repo that knows
its own build wiring wins.

## The skills

| Skill | What it does |
|---|---|
| [`android-screenshot-baseline-record`](skills/android-screenshot-baseline-record/README.md) | Record golden images and prove files were written — `git status` on the baseline directory, not the build's exit code |
| [`android-screenshot-baseline-verify`](skills/android-screenshot-baseline-verify/README.md) | Run the *verify* task, then confirm comparisons actually happened before reporting a pass |
| [`figma-to-compose-component`](skills/figma-to-compose-component/README.md) | Build a Compose component from a Figma node — after checking the design system doesn't already have it — bound to theme tokens, covered by a screenshot test |
| [`android-verify-on-device`](skills/android-verify-on-device/README.md) | When no test can hold the claim: drive a real device without trusting a stale frame, a missed tap, or a capture of the wrong screen |

Each skill's README carries its triggers and a worked example; the `SKILL.md`
beside it is the procedure the agent follows.
