# coverage-pr-comment

Turns a coverage report into **one** pull-request comment that a reviewer can act
on: a headline percentage, a bar that doubles as a diff against the base branch,
a threshold band naming where the project stands, and a per-metric table with a
status column.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it produces and
how to reach it.

## Using it

Ask for it in any of these shapes; the skill fires on the intent, not on a
command:

- "post coverage on the PR"
- "the coverage bot adds a new comment on every push"
- "show the coverage delta against the base branch"
- "add a red-amber-green threshold to the coverage comment"

It is stack-agnostic. Only the first step differs between projects: reading the
totals out of a JaCoCo XML, an Istanbul `coverage-summary.json`, a Cobertura
file, a `go tool cover` run, `.last_run.json` or an `lcov.info`. Everything after
that is identical, because the skill normalises to `{metric: (pct, covered,
total)}` before it renders anything.

Two knobs you set per project: a **floor** and a **target** for each metric. The
floor is what turns a row red, the target is what turns it green, and everything
between is amber.

```python
THRESHOLDS = {          # branch coverage runs below line coverage in every
    "line":   (40, 60), # codebase, so one pair for all metrics would paint the
    "branch": (25, 45), # branch row permanently red
}
```

## What it looks like

The comment on a pull request, after two pushes, still one comment, edited in
place:

> ## Coverage: 47.3% of lines (▲ +6.1 vs main)
>
> 🟦🟦🟦🟦🟦🟦🟦🟦🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜
>
> **1841/3890 lines**
>
> 🟡 **Approaching target** — 12.7 points below the 60% line target
>
> | Metric | Base | Head | Δ | Status |
> |---|---:|---:|---:|:--:|
> | Line | 41.2% | 47.3% | ▲ +6.1 | 🟡 |
> | Branch | 25.1% | 24.4% | ▼ -0.7 | 🔴 |
>
> <sub>🟦 covered on main &nbsp; 🟩 added here &nbsp; 🟥 removed here &nbsp; ⬜ uncovered</sub>
> <sub>🔴 below floor · 🟡 below target · 🟢 at target — line 40/60, branch 25/45</sub>

That is the live markdown, not a screenshot: GitHub renders it here exactly as
it renders in the comment, so this preview cannot drift from the format the skill
produces. The same body was posted to a real pull request while writing this, and
posted a second time, to confirm the upsert edits one comment instead of adding a
second.

Source, for copying:

```markdown
<!-- coverage-report -->
## Coverage: 47.3% of lines (▲ +6.1 vs main)

🟦🟦🟦🟦🟦🟦🟦🟦🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜

**1841/3890 lines**

🟡 **Approaching target** — 12.7 points below the 60% line target

| Metric | Base | Head | Δ | Status |
|---|---:|---:|---:|:--:|
| Line | 41.2% | 47.3% | ▲ +6.1 | 🟡 |
| Branch | 25.1% | 24.4% | ▼ -0.7 | 🔴 |

<sub>🟦 covered on main &nbsp; 🟩 added here &nbsp; 🟥 removed here &nbsp; ⬜ uncovered</sub>
<sub>🔴 below floor · 🟡 below target · 🟢 at target — line 40/60, branch 25/45</sub>
```

Reading it: eight blue blocks of coverage `main` already had, one green block
this branch added, eleven still uncovered. Line coverage rose 6.1 points and is
amber: clear of its 40% floor, short of its 60% target. Branch coverage fell
0.7 and crossed **below** its floor, which is the row that should stop the merge.

Each block is 5 points at width 20, so a sub-5-point move shows as a colour that
does not change; the delta and the table carry that, which is why the comment
has all three.

## Why it is shaped like this

- **Emoji blocks, not a chart.** GitHub strips inline SVG from comments and has
  no syntax for coloured text. Coloured emoji are the only coloured mark that
  survives inside a table cell.
- **A delta, not just a number.** `47.3%` answers nothing. `▲ +1.2 vs main` does.
- **`1841/3890`, not just `47.3%`.** A percentage alone hides a codebase that
  shrank: delete an untested module and coverage "improves".
- **A status column that can fail the build.** The skill's step 5 insists the
  floor either fails a step or is labelled advisory. A colour that can never stop
  anything trains reviewers to skip the comment.

## Related

- `pr-comment-loop`: replying to review findings, one row per finding.
- `github-pr-screenshot-embed`: the host rule for images that render for
  reviewers on a private repo.
