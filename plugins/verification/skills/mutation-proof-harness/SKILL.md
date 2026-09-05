---
name: mutation-proof-harness
description: >
  Use when about to prove that newly added guards can fail — a checker, a lint,
  a CI script, a validation function — and more than one needs proving. Fires on
  "prove the check can fail", "mutation proof", "watch it go red", and whenever
  a PR test plan is about to claim a guard was proved. Owns the SCRIPT: the
  baseline that stops a typo'd filter reading as a pass, the diff that stops a
  no-op mutation reading as a working guard, and the restore. Do NOT fire for a
  single ad-hoc mutation, or to decide WHETHER a guard is worth proving —
  prove-the-check-can-fail owns that.
---

# Mutation proof harness

`prove-the-check-can-fail` says an assertion never watched to fail is
decoration. This is the loop that watches, for more than one guard at a time.

The reason it is a script and not a habit: hand-driving it produces two failure
modes that both **look like success**. A test filter matching nothing reports a
pass. A mutation that edits the file without changing behaviour reports a pass.
Both are silent, so the tally reads the same either way.

## Procedure

### 1. Commit first

`git checkout -- <file>` restores from the **index**, not from HEAD. So work
that was staged but never committed survives the restore and stays staged, and
step 6's clean-tree check then reads as a failed restore when nothing failed;
work that was never staged is simply gone. Commit or stash pending work before
mutating anything, and the question does not arise.

### 2. Define the two things the rest depends on

One command that runs the suite filtered to a single test name, and the list of
names. Everything below is written against these two.

```bash
W=/abs/path/to/worktree                 # absolute: cwd resets between calls
cd "$W" || exit 1
pass=0; bad=0

# The one line to adapt per project. Must exit non-zero when the test fails.
# Use the repo's own pinned test command. A bare `npx <runner>` resolves from
# the registry when no local binary exists, which downloads and executes a
# package this script never chose.
run_filter () { (cd "$W/scripts" && npm test --silent -- -t "$1" 2>&1); }
#   pytest:  (cd "$W" && python -m pytest -q -k "$1" 2>&1)
#   go:      (cd "$W" && go test ./... -run "$1" 2>&1)

# One row per guard: the file to mutate, the substitution, the test name that
# must go red, and a label for the log.
GUARDS=(
  "src/check.ts|s{exit 1}{exit 0}|refuses a drop|drop guard exits non-zero"
  "src/check.ts|s{-eq 0}{-eq 999}|refuses an empty directory|empty dir is not clean"
)
FILTERS=(); for g in "${GUARDS[@]}"; do IFS='|' read -r _ _ f _ <<< "$g"; FILTERS+=("$f"); done
```

### 3. Prove the baseline: every filter green AND non-empty

The half that is always skipped. A filter that selects no tests exits 0, so the
mutation that follows is measured against nothing.

```bash
for f in "${FILTERS[@]}"; do
  out=$(run_filter "$f")
  [ $? -eq 0 ] || { echo "ABORT baseline red: $f"; exit 1; }
  printf '%s' "$out" | grep -qE 'Tests +0 passed|No test files found' \
    && { echo "ABORT filter selects nothing: $f"; exit 1; }
done
```

Adapt the grep to the runner's "nothing ran" wording — it differs per tool and
is the one string this depends on.

### 4. Mutate, diff, run, restore

```bash
mutate () {                      # <file> <perl-expr> <filter> <label>
  # An interrupt between the edit and the restore leaves the guard mutated in
  # the working tree, and the tally never prints, so nothing points at it.
  trap 'git checkout -- "$1"; trap - INT TERM; return 130' INT TERM
  # `-pi` is line-at-a-time. Use `-0pi` when the anchor spans lines — and then
  # read the warning about first-match below, which only bites in that mode.
  perl -pi -e "$2" "$1"
  if git diff --quiet -- "$1"; then echo "STALE $4"; bad=$((bad+1)); return; fi
  git diff --unified=0 -- "$1" | tail -4        # ← read this, every time
  local out code; out=$(run_filter "$3"); code=$?
  git checkout -- "$1" || { echo "RESTORE-FAILED $4"; bad=$((bad+1)); return 1; }
  # Red is not proof on its own. A compile error, a missing import or a
  # collapsed fixture also exits non-zero, and counting one as proof is how an
  # inert guard gets reported as proved. Require the failure to name the test
  # the filter selected.
  if [ $code -ne 0 ] && printf '%s' "$out" | grep -qF "$3"; then
    echo "OK    $4"; pass=$((pass+1))
  elif [ $code -ne 0 ]; then
    echo "WRONG-RED $4 (failed, but not in $3)"; printf '%s\n' "$out" | tail -6
    bad=$((bad+1))
  else
    echo "GREEN $4"; printf '%s\n' "$out" | tail -4; bad=$((bad+1))
  fi
}
```

`git diff --quiet` catches only the total misses. The printed diff is what
catches the mutation that changed the wrong line, which `--quiet` calls a
success.

Then walk the table:

```bash
for g in "${GUARDS[@]}"; do
  IFS='|' read -r file expr filter label <<< "$g"
  # An interrupted or failed-restore mutation returns non-zero, and ignoring it
  # lets the run reach a clean-looking tally with a mutated file still on disk.
  mutate "$file" "$expr" "$filter" "$label" || { echo "ABORT during $label"; break; }
done
```

### 5. Treat GREEN as unproven, not as a pass

Suspect the mutation before the test, and check these four in order:

| Cause | Check |
|---|---|
| The edit was a no-op | Does the new value differ from the old at runtime? `max = Math.max(max, 0)` where `max >= 0` changes nothing |
| The real guard is still upstream | Did an earlier `if (…) continue` / early return already handle the case? |
| First-match hit the wrong branch | Under `perl -0pi`, only the first match is replaced. Is your anchor text unique to the branch, or contained in another? |
| The test never imports that file | Does the filter's test import the file you mutated, or a sibling that re-exports the same name? |

Retarget and re-run. Report the retarget in the PR test plan: "eight of nine
went red first time" is what makes the ninth worth reading.

### 6. Report the count, and that the baseline ran

```bash
echo "proved-able-to-fail: $pass   not-proved: $bad"
# `git status --short` prints a dirty tree without failing on one, so a
# mutation left behind would still exit zero. Assert emptiness instead.
[ -z "$(git status --porcelain)" ] \
  || { git status --short; echo "ABORT tree not restored"; exit 1; }
[ "$bad" -eq 0 ]            # the script's own exit status
```

`$pass` and `$bad` are the counters Step 4 increments. A tally without Step 3's
baseline line above it is not evidence.

## Perl expressions that silently do nothing

Each cost a round to diagnose:

- **`\Q…\E` does not stop interpolation.** `\Q(?<![A-Za-z0-9_.$])\E` expands
  `$]` to the Perl version. `${#files[@]}` and `${VAR:?…}` expand too. Escape
  the `$`, or anchor on a fragment without one.
- **`/` as the delimiter fights the content.** Use `s{…}{…}` when the target
  holds a regex, a path or a URL.
- **`-0pi` slurps and replaces once.** In that mode add `/g` deliberately, or
  make the anchor unique — not merely distinctive-looking.
- **A single-quoted shell string cannot hold a single quote.** Switching to
  double quotes adds a second expansion layer, and the escapes are per layer:
  `\$` is consumed by the shell and reaches perl as a bare `$`, which perl then
  interpolates — the failure this list opens with. Perl's own `\$` needs
  `\\\$` written in the double-quoted string. `${VAR:?…}` is worse: it aborts
  the shell when the array is *defined*, before any mutation runs. Prefer an
  anchor with no quotes and no `$` in it.

## When to STOP

- **Only one guard to prove** — do it inline; a script for one mutation is
  ceremony.
- **The baseline is red** before any mutation. Fix that first; mutating a
  failing suite measures nothing.
- **A mutation cannot be expressed as a text substitution** — a behaviour that
  needs a different fixture or a stubbed clock is a test to write, not a
  mutation to make.
- **The file is not committed.** Step 1, and it is not negotiable: the restore
  is destructive.
