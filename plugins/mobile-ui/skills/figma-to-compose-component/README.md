# figma-to-compose-component

Builds a Jetpack Compose component from a Figma design without the two
expensive mistakes: fetching a whole Figma file when one node was needed, and
building a component the design system already has. The most costly outcome is
not a bad component — it is a *duplicate* one, invisible until the catalogue
has three near-identical buttons.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it looks like in
use and how to reach it.

## Using it

Fire when a `figma.com/design` or `figma.com/file` link is paired with:

- "build this"
- "implement this component"
- "recreate this in Compose"
- a ticket referencing a Figma node id

It deliberately does **not** fire when the project ships its own design-system
skill — that one knows its component catalogue and retrieval order.

## Example

A ticket links a badge design with `node-id=42:1337`:

1. **Read the node, not the file** — a file fetch returns megabytes of
   unrelated frames. Request the node's metadata, its variant set, and one
   rendered image, in that order, stopping when there is enough. No Figma
   integration available → ask for the values; never infer hex colours from a
   compressed screenshot.
2. **Search the design system first** — find the module the theme lives in
   (that *is* the design system, whatever it is called; a single-module app is
   a smaller design system, not a missing one), then decide explicitly:
   exists-and-fits (use it, stop), nearly fits (extend with a variant —
   cheaper than a sibling), or genuinely new (build it, in the design-system
   module if reusable).
3. **Map every Figma value to a token** — with a custom scale, raw `.dp` /
   `Color(0x…)` in the finished component are the defect; with Material only,
   `MaterialTheme.colorScheme/typography/shapes` are the tokens and raw
   spacing is correct, not a defect. A value sitting between two tokens is a
   question for the designer, not a rounding call.
4. **Build it stateless with a `@Preview` per state** — the preview is what
   the screenshot test captures, so a state without a preview is a state
   without coverage.
5. **Cover with a screenshot test and record baselines** — recording is what
   proves the capture picked up the theme rather than rendering unstyled.
6. **Compare against the design** — proportions, spacing, typography, colour,
   corners, in that order; a deliberate deviation stated is fine, an unnoticed
   one is a defect.

## Related

- [`android-screenshot-baseline-record`](../android-screenshot-baseline-record/README.md) —
  step 5's hand-off for recording the new component's baselines.
- [`android-screenshot-baseline-verify`](../android-screenshot-baseline-verify/README.md) —
  keeps those baselines honest on every later change.
