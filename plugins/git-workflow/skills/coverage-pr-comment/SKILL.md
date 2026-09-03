---
name: coverage-pr-comment
description: >
  Use when reporting code coverage on a pull request, or fixing a report that is
  not landing. Fire when the user says "post coverage on the PR", "show the
  coverage delta against the base branch", "the coverage bot adds a new comment
  every push", "add a threshold / red-amber-green band to coverage", "coverage
  dropped and nobody noticed", or when a PR carries a bare coverage percentage
  that no reviewer acts on. Stack-agnostic — JaCoCo, lcov, Istanbul, coverage.py,
  go cover, SimpleCov, coverlet. Skip for GitLab MRs, whose discussion API needs
  its own upsert; when Codecov or Coveralls already comments, stop and ask
  before adding a second (see When to STOP).
---

# Coverage comment on a pull request

A coverage comment fails in two ways, and neither one looks like a failure:

1. **It appends instead of editing.** Ten pushes, ten comments, and the review
   thread is unreadable. Fixed by a marker and an upsert (step 4).
2. **It reports a number with no verdict.** `47.3%` answers nothing a reviewer
   can act on — is that good, is it falling, is it about to break a rule? Fixed
   by a delta against the base and a threshold band (steps 2 and 5).

The output is one sticky comment carrying a headline percentage, a bar that
doubles as a diff, a **band line** naming where the project stands, and a
per-metric table with a **status column**.

## Procedure

### 1. Get the numbers

Every stack can emit a machine-readable report. Parse that, never the human
summary — its layout changes between tool versions without notice.

| Stack | Report to generate | Totals live at |
|---|---|---|
| JVM — JaCoCo | `jacocoTestReport` → `jacocoTestReport.xml` | root `<counter type="LINE" missed= covered=>` |
| JS/TS — Istanbul (jest, vitest, nyc) | `--coverage --coverage-reporters=json-summary` | `coverage/coverage-summary.json` → `.total.lines.pct` |
| Python — coverage.py | `coverage xml` | `coverage.xml` (Cobertura) → `line-rate`, `branch-rate` |
| .NET — coverlet | `--collect:"XPlat Code Coverage"` | `coverage.cobertura.xml`, same shape |
| Go | `go test -coverprofile=c.out` then `go tool cover -func=c.out` | the trailing `total:` line |
| Ruby — SimpleCov | default run | `coverage/.last_run.json` → `.result.line` |
| C/C++/Swift/JS — lcov | `lcov.info` | sum the `LF:` and `LH:` records |

Normalise whatever you parse into one shape — `{metric: (pct, covered, total)}` —
so the renderer below never learns which stack it is serving.

**Carry `covered/total`, not just the percentage.** A percentage alone hides a
codebase that shrank: delete a poorly covered module and coverage "improves"
while nothing was tested.

### 2. Get the base number too

The delta is the part reviewers read. Get the base branch's figure from a stored
artifact published by the base branch's own runs — rebuilding coverage for the
merge target doubles every PR's CI time. Concretely: the base branch's push
workflow uploads the normalised totals (`actions/upload-artifact` with a fixed
name, say `coverage-baseline`, holding the totals JSON); the PR job pulls the
newest one:

```bash
run=$(gh run list -b "$BASE" -w "$WORKFLOW" -s success -L 1 \
        --json databaseId -q '.[0].databaseId')
[ -n "$run" ] && gh run download "$run" -n coverage-baseline -D baseline/
```

An empty `$run` or a failed download is the missing-baseline case below — fall
through, never fail.

**A missing baseline is not an error.** First run, a new base branch, an expired
artifact: degrade to absolute figures and say so. Never fail the job, and never
print a delta you could not compute.

**If the repo insists on a delta where no artifact can exist** — stacked PRs,
whose base is a feature branch no push run ever measured — the fallback is
rebuilding the base in the PR job, and two rules keep that delta honest:

- **Both runs must measure the same file set with the same tool versions.**
  Copy the head's coverage config over the base checkout before running it;
  two configs that differ in `include` or `all` produce a delta with no
  meaning that looks exactly like a real one.
- **Give the base run the head's package manifests and lockfile, never a
  hand-pinned dependency list.** A pinned list must be re-synced on every
  dependency bump, and the tolerated-failure guard hides the rot: the delta
  quietly becomes the missing-baseline dash, which reads as a base problem.
  Borrowing the manifests leaves one honest residual — a PR that removes a
  dependency the base still imports loses its delta, and deserves to.

### 3. Render it

Three functions carry all the nuance; the rest is string formatting.

```python
COVERED, ADDED, LOST, EMPTY = "🟦", "🟩", "🟥", "⬜"

def bar(pct, base_pct=None, width=20):
    """Blue = already covered on the base, green = added here, red = removed here."""
    head = round(pct / 100 * width)
    if base_pct is None:
        return COVERED * head + EMPTY * (width - head)
    base = round(base_pct / 100 * width)
    if head >= base:
        return COVERED * base + ADDED * (head - base) + EMPTY * (width - head)
    return COVERED * head + LOST * (base - head) + EMPTY * (width - base)

def band(pct, floor, target):
    """(mark, name) for one metric against its own two thresholds."""
    if pct < floor:
        return "🔴", "Below floor"
    if pct < target:
        return "🟡", "Approaching target"
    return "🟢", "At target"

def delta(head, base):
    if base is None:
        return "new"
    diff = head - base
    return "—" if abs(diff) < 0.05 else f"{'▲' if diff > 0 else '▼'} {diff:+.1f}"
```

Emoji blocks are not a style choice. GitHub strips inline SVG from comments and
has no syntax for coloured text, so **coloured emoji are the only coloured mark
that survives inside a table cell**. They also render about twice as wide as a
character — a bar that reads well at 20 blocks in the headline needs half that
inside a table column.

`delta` needs the epsilon. Without it, a rounding wobble of 0.02 points prints
`▼ -0.0` and reviewers learn to ignore the arrow.

Assemble in this order — headline, bar, denominator, band line, table:

```markdown
## Coverage: 47.3% of lines (▲ +6.1 vs main)

🟦🟦🟦🟦🟦🟦🟦🟦🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜

**1841/3890 lines**

🟡 **Approaching target** — 12.7 points below the 60% line target

| Metric | Base | Head | Δ | Status |
|---|---:|---:|---:|:--:|
| Line | 41.2% | 47.3% | ▲ +6.1 | 🟡 |
| Branch | 25.1% | 24.4% | ▼ -0.7 | 🔴 |

<sub>🔴 below floor · 🟡 below target · 🟢 at target — line 40/60, branch 25/45</sub>
```

Put per-file or per-package rows inside `<details>`. They are the longest part of
the comment and the least read.

### 4. Post it sticky

The marker is an HTML comment, so it is invisible in the rendered body and still
findable in the raw one.

```bash
marker='<!-- coverage-report -->'
{ echo "$marker"; cat coverage.md; } > comment.md
id=$(gh api --paginate "repos/$REPO/issues/$PR_NUMBER/comments" \
       --jq ".[] | select(.body | startswith(\"$marker\")) | .id" | tail -n 1)
if [ -n "$id" ]; then
  gh api --method PATCH "repos/$REPO/issues/comments/$id" -f body="$(cat comment.md)" > /dev/null
else
  gh pr comment "$PR_NUMBER" --body-file comment.md
fi
```

**List through the REST API, not `gh pr view --json comments`.** That returns
GraphQL node ids (`IC_kwDO…`), and the REST edit endpoint rejects them with a
404 that reads like a missing comment rather than a wrong id.

In CI the job needs `permissions: pull-requests: write`, and workflow context
belongs in `env:` rather than interpolated into the script, where a branch name
would be read as shell.

### 5. Make the band mean something

A status column that can never fail anything is decoration, and a decorative
column teaches reviewers to skip the whole comment. Pick one and be explicit:

- **Gate it.** The same floor that colours the row also fails a step. Read both
  from one place, so the comment cannot say 🔴 while the build says green — in
  practice: the thresholds live in one file (say `coverage-thresholds.json`),
  and the render script that reads it for the band also exits non-zero when a
  gated metric sits below its floor, so the CI step fails from that same read.
- **Or label it advisory** in the legend, and say what will act on it instead.

Set the floor at or just below **current** coverage and raise it as coverage
rises. A floor above today's number reds every pull request from day one,
including the ones that improve things — the ratchet (floor = the base branch's
figure, so coverage may not fall) is usually the honest version of what people
mean by "we should have a threshold".

## Thresholds that bite

- **One pair of numbers for every metric paints branch coverage permanently
  red.** Branch coverage runs well below line coverage in every codebase. Give
  each metric its own floor and target.
- **Percentage bands on a tiny diff swing wildly.** A 3-line PR can move a small
  module by 12 points. Band the project total; leave per-file rows uncoloured.
- **Say what the numbers are** in the legend. A bare 🟡 sends the reader to look
  for the config file that defines it.
- Coverage that cannot move (a docs-only change) should reuse the previous
  comment rather than recompute — but never delete it, or the PR looks unmeasured.

## When to STOP and ask

- **The pull request comes from a fork.** Its `pull_request` token is read-only,
  so the post step fails. Switching to `pull_request_target` is not a fix to
  make quietly: it runs base-branch code with a write token against untrusted
  input. Surface the trade-off and let the user choose.
- **Codecov, Coveralls or a similar app already comments.** A second comment is
  noise. Ask whether to replace the existing one or drop this.
- **The user wants a floor above current coverage.** Confirm they intend every
  open pull request to go red immediately, and offer the ratchet instead.
- **The floor will fail other people's builds.** Confirm the number with whoever
  owns the repo before wiring the gate — a threshold is a policy, not a format.
- **There is no coverage report at all.** Producing one is a separate piece of
  work with its own trade-offs. Do not bolt a coverage tool onto the build to
  satisfy a request for a comment.
