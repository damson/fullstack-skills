# diagnose-a-lying-signal

For the moment a status surface and reality disagree: a green check for work
that cannot have happened, a badge that stays "unknown" after the thing everyone
blamed was fixed, a run that failed with nothing in it, a command that reports
no matches it should have found. It sends you to the authoritative record before
you debug anything, because in this class of problem the work is usually fine
and the reporter is not.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

Say any of these; the skill fires on the intent, not on a command:

- "the check is green but nothing was uploaded"
- "the badge still says unknown"
- "why did that fail, there is nothing in the log"
- "that number cannot be right"

It stays quiet for an honest failure. A real error in a real log is debugging,
and the log is already telling the truth.

## Why a separate skill

Proving a check *can* fail is a different job, done at a different time: that is
proactive, before you trust a new assertion. This one is reactive, for a signal
already in front of you that cannot be true. The two share a worldview and
nothing else.

## The shape it keeps catching

Four real examples, all from one afternoon:

- A coverage step reported success on every run while uploading nothing. The
  upload failed inside an action configured not to fail the job, so the error
  lived only in the step's own log.
- A badge read "unknown" for hours after the service was activated. The data
  existed; the badge was scoped to a branch that nothing ever uploads to.
- A pull request showed two red checks whose runs contained zero jobs. The
  workflow files were provably fine; the checks had started before the merge ref
  existed.
- A grep for a percentage in a badge returned `100%`. It had matched `y2="100%"`
  in the SVG's gradient definition.

Each cost real time, and in each the underlying work was correct.

## Example

```
> the coverage badge still says unknown, I signed in

Stating it: the badge reports unknown, but the API holds a completed report at
63% for this repo. Both cannot describe the same thing.

Surface: the badge URL. Source: the coverage API's commit records.
The API has develop at 63%, complete. The default branch has no record at all.
The badge asks for the default branch, and the workflow uploads only from
develop and pull requests.

Two separate findings: the badge is pointed at a branch nothing uploads to
(a display bug, one line), and the release branch genuinely has no coverage
data (a pipeline decision, yours to make).
```
