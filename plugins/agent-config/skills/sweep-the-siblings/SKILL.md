---
name: sweep-the-siblings
description: >
  Use when a defect turns up in one member of a family of sibling documents —
  a skill page, a runbook, an ADR, a workflow file, a per-package README — and
  the family shares an invariant the repo states somewhere. Fires on "is that
  wrong anywhere else?", on filing an issue for a single instance, and after a
  reviewer finds a fault that is about form rather than content. Do NOT fire
  when the repo states no invariant to sweep against, when the family has
  fewer than three members, or for a defect genuinely local to one file.
---

# Sweep the siblings

A review finding on one file is a hypothesis about every file like it. Reviewers
read a diff, so they can only report the instance in front of them; the same
omission usually sits in the siblings nobody changed this week, where it will be
found one at a time, by one reader each, for as long as nobody looks.

The failure this prevents is the slow leak: a rule the project states, honoured
in the files that happen to get touched, quietly false everywhere else. The one
that makes a sweep worth doing carefully is its opposite: a grep proposes
candidates confidently and is wrong about a third of them, so a sweep that
trusts its own output ships a diff that "fixes" files that were already correct.

## Procedure

1. **Quote the invariant in the repo's own words before looking for breaches.**
   It lives in a contributing guide, a `CLAUDE.md`, a pull-request template, or
   a validator's error strings:

   ```bash
   grep -rniE "must|always|every .* (has|carries|states)" CONTRIBUTING* CLAUDE.md AGENTS.md .github/ docs/ 2>/dev/null | head
   ```

   If the rule is your inference rather than the project's, stop and propose it
   as a rule first. A sweep is enforcement, and enforcing a preference nobody
   agreed to is how a repo acquires a convention by ambush.

2. **Define the family by what the invariant governs**, not by directory
   convenience: every skill page, every workflow, every package README. Fewer
   than three members is not a family; fix the one file and move on.

3. **Sweep mechanically, and treat the output as candidates.** Cheap and
   exhaustive beats clever: a missing section, a banned character, a command
   that does not exist on a platform the project supports.

   ```bash
   for f in <family glob>; do
     grep -q '^## Example' "$f" || echo "  candidate: $f"
   done
   ```

   Sweep for the *absence* where you can. A grep for the correct form finds
   files that already comply; a grep for the broken form only finds the
   spellings you thought of.

4. **Read every candidate before believing it.** This is the step the whole
   procedure exists for, and skipping it is what turns a sweep into noise. Real
   false positives look like this: a rule satisfied in words the pattern did not
   contain ("use X instead" is a boundary; the grep wanted "do not"); a section
   present under a heading of its own ("What it looks like" is an example); a
   command that is fine because it only ever runs where it exists. Expect a
   third of the list to survive.

5. **Fix what survives in one pull request, and publish both numbers.** How many
   candidates the sweep produced and how many were real is the reviewer's only
   defence against a mechanical diff: "4 of 5, and the fifth already complied
   under its own heading" is checkable, "swept the tree" is not. Take whatever
   bookkeeping the repo attaches to a changed file (a version bump, an index
   entry, a count in a README) in the same PR.

6. **Say what the sweep could not see.** A pattern cannot tell whether an
   example is real, whether a command was ever run, or whether prose still
   matches the procedure beside it. Naming the blind spot is what stops the next
   reader treating a clean sweep as a clean bill of health.

## When to STOP

- **The invariant is yours, not the repo's.** Propose the rule, get it agreed,
  sweep afterwards.
- **A candidate's fix would change behaviour rather than form.** That is its own
  change with its own review; note it and leave it out of the sweep.
- **The sweep comes back empty.** Report that. A clean sweep is a result, and it
  is worth more than a sweep nobody ran, but it is not worth a diff.
- **Every candidate turns out to be a false positive.** The pattern was wrong,
  not the files. Fix the pattern or drop the sweep; do not go looking for
  something else to change to justify the run.
- **A file in the family belongs to someone else's in-flight branch.** Sweeping
  it means editing under them; list it for the owner instead.
