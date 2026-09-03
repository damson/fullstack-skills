# validate-skill-against-real-project

Takes a portable skill that has only ever been *read* and runs its commands
verbatim against a real project in its claimed scope. The failure it prevents:
a skill that reads as correct long after it stopped being — task names
inverted, a flag that turns out to be a GNU extension, a grep that returns
nothing on a layout the author never had. None of that is visible by reading;
the sentences stay plausible.

Read [SKILL.md](SKILL.md) for the procedure.

## Using it

- "validate the skill" / "does this skill actually work?"
- "test it against a real repo"
- a skill claims to work on "any \<stack\> project" and no run is on record
- a skill was reviewed by reading it rather than running it

It skips project-specific skills — those are allowed to assume one build's
wiring.

## Example

Validating a screenshot-testing skill that claims "any Android/Compose
project":

1. Pick the **smallest** in-scope project — the small end is where generic
   skills break, because the author's own project was never there.
2. Extract every executable claim: commands and their flags, predicted task
   and directory names, "tool X rejects Y" assertions.
3. Run each one **verbatim** — an adapted command validates the adaptation,
   not the skill — capturing exit codes before piping (a pipeline reports its
   last command).
4. Check tool claims against the actual binary (`command -v`, version): a
   friendlier drop-in on `$PATH` accepts syntax the stock tool refuses.
5. Exercise the degenerate cases with a `mktemp -d` empty repo and a fresh
   `--depth 1` clone that has never been built: a discovery step with no
   branch for "nothing found" is a defect even when its happy path works.
6. Report one issue per skill in the owning repo, titled
   `skill: <name> — <what breaks>`, quoting the skill's line, the command run,
   its exit code and output, and what it costs someone following it — via the
   forge's own CLI, or a local report file when no forge CLI is available.

One boundary it draws explicitly: having read the skill, you can judge whether
its commands run — you can no longer judge whether it would have *fired*
unprompted or been followed correctly. That half is left to a session without
this context, and the report says so.

## Related

- `verification:prove-the-check-can-fail` — same discipline one level down:
  this skill validates a procedure, that one validates a single check by
  breaking what it guards.
- `skill-opportunity-finder` — proposes new skills; this skill is how a
  proposed-and-written one earns trust before being relied on.
