# sweep-the-siblings

Turns a single review finding into a question about every file like it, then
answers that question carefully enough to be trusted. A reviewer reads one diff
and reports one instance; the same omission usually sits in the siblings nobody
touched, where it gets found one reader at a time.

The trap it exists for is not the sweep, it is the sweep's confidence. A pattern
proposes candidates and is wrong about a third of them, so a run that trusts its
own output ships a diff that changes files which already complied.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

- "is that wrong anywhere else?"
- "check the rest of them for the same thing"
- a reviewer's finding that is about form rather than content
- filing an issue for one instance of something that has a general rule behind
  it

It does not fire when the project states no rule to sweep against, when the
family has fewer than three members, or for a defect that is genuinely local to
one file.

## Example

A reviewer notes that one page lists triggers and failure modes but never shows
the thing being used, and the project's own contribution guide asks every such
page for a worked example. That is a rule plus a family, so it is a sweep.

The mechanical pass checks all 34 pages for the three sections and returns five
candidates. Reading them is what makes the result usable: four are real, and the
fifth carries all three sections under headings of its own choosing, so the
pattern was wrong about it and the file is left alone.

The pull request says exactly that, "five candidates, four real, the fifth
already complies under its own heading", which a reviewer can check in a minute.
It also says what the sweep could not see: a grep knows whether an example
exists, never whether the example is real.

The same shape ran twice more that day. Thirty-four descriptions checked for a
stated boundary, three real and one satisfied in different words. Every embedded
command checked against the platforms the project supports: three broken on one
platform or the other, one cleared by running it.

## Related

- `agent-config-audit` (this plugin): the neighbouring case, where the question
  is whether the instruction files contradict each other rather than whether
  each one satisfies a stated rule.
- `redundancy-check-before-ship` (this plugin): the single addition, before it
  becomes one of the siblings.
- `pr-comment-loop` (git-workflow plugin, if installed): where the finding that
  starts a sweep usually arrives, and where its verdict is recorded.
- `prove-the-check-can-fail` (verification plugin, if installed): the same
  refusal to trust a mechanical result without watching it behave.
