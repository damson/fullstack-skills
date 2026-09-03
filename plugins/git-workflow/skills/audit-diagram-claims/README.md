# audit-diagram-claims

Treats an architecture diagram as a set of claims, not a set of shapes. "Did a
box move?" can be answered without opening the file, which is exactly why
diagrams rot: the shapes stay stable while the words inside them go false. This
skill lists what every node label asserts, checks each assertion against the
code, and asks the question no diff can answer: what does the map not mention
at all?

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

Fires before ticking any "architecture updated" / "diagram updated" checkbox,
and whenever a change alters a cadence, a pipeline stage, a guarantee, a count,
or introduces a subsystem. Also on:

- "did you check the diagram?"
- "is the diagram stale?"
- "isn't there a diagram change here?"

It does not fire for changes with no behavioural surface: typo fixes,
test-only diffs, dependency bumps, formatting. Ticking nothing and saying why
beats performing an audit to justify a checkbox.

## Example

A PR changes a cron schedule. The skill:

1. Finds the diagram file(s): the one the PR template names, else a grep for
   mermaid/plantuml/drawio blocks.
2. Writes out each node's claims by shape: cadence (`weekly cron`), count
   (`8 channels`), stage list, guarantee (`refuses to write if a slug would
   collide`), routing. Guarantees get checked first: they are added by the PRs
   least likely to think about pictures.
3. Checks each claim against reality, not against the diff (a label goes stale
   from someone else's merge as readily as yours), including the prose beside
   the diagram, which restates the same claims and rots independently.
4. Enumerates the repo's units (directories, scheduled workflows) and greps the
   diagram for each name. **A name with zero hits is a reportable gap**: the
   one signal a code review cannot give, because no diff shows a subsystem that
   was never drawn.
5. Makes the smallest true edit, renders the result, and proves the render
   check can fail by breaking the diagram on purpose: `flowchart TB` →
   `flowchart ZZ`, which reliably exits 1. Not every mutation works: corrupting
   `-->` to `--` leaves a *valid* diagram and a green check, a trap this very
   skill recommended until 2026-09-02.
6. Reports the claims verified, not "diagram updated": "checked cadence, count
   and the two guarantees; added the missing discovery node" is auditable.

## Related

- `verification` plugin's `prove-the-check-can-fail`: step 5 is that
  discipline applied to diagram rendering.
- `pr-comment-loop`: where the audit's outcome lands when a reviewer asked
  for it.
