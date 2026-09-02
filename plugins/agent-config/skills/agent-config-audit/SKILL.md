---
name: agent-config-audit
description: >
  Audit AI agent configuration files (CLAUDE.md, AGENTS.md, preferences.md) for contradictions,
  duplication, bloat, and personal/team boundary violations. Use when unsure which instruction
  files are active for a project, after restructuring a config repo, or when the same rule
  turns up in two files with different wording.
---

# Agent Config Audit

Audit the AI instruction files active for the current project. Report findings, optionally fix them.

## Step 1: Resolve the Active File Stack

From the current working directory, resolve the project's instruction-file
stack — items 1, 3 and 4 are loaded by the harness; 2 and 5 are audited when
present (all five resolved; scoping flags filter afterwards — see Flags):

1. **Global CLAUDE.md** — `~/.claude/CLAUDE.md` (follow symlink to source)
2. **Global preferences** — `~/.claude/preferences.md`, if present
3. **Project AGENTS.md** — look for `AGENTS.md` in the project root (follow symlink to source)
4. **Project CLAUDE.md** — look for `CLAUDE.md` in the project root (follow symlink chain fully)
5. **Project preferences** — `.claude/preferences.md` in the project root, if
   present

For each file found, report:
- The logical path (e.g. `<project>/AGENTS.md`)
- The resolved source path (e.g. `<config-repo>/workspace/<domain>/AGENTS.md`)
- Whether it is personal or team-owned. The rule: a file that resolves into
  the user's config repo or lives under `~/.claude/` is personal; a file
  tracked directly in the project repo is team-owned

Print the stack before running checks so the user knows the scope.

## Step 2: Run Checks

For each finding, record: severity (`🔴 Contradiction` / `⚠️ Duplication` / `📦 Bloat` / `🚧 Boundary violation` / `✅ OK`), file + section, and a recommended fix.

### 2a — Personal/Team Boundary

Team files (`AGENTS.md` in the project repo) should contain **only** team conventions — rules agreed upon by the whole team. Flag any of the following if found in a team file:

- Personal commit style preferences (e.g. no pod prefix, "Extract" wording)
- No-AI-signature rules
- Worktree tool commands (`git gtr`, etc.)
- Personal story point sizing
- Personal tool shortcuts or aliases

### 2b — Contradictions

For each topic that appears in multiple files (commit format, naming, testing framework, etc.), compare the rules:

- If the rules agree → `✅ OK`
- If they differ, it is **intentional layering** only when a verified mechanism reinstates the team rule downstream; with no such mechanism it is a **genuine conflict**
- Flag genuine conflicts as `🔴 Contradiction` with both locations and both values

Example of intentional layering (not a conflict):
> Team AGENTS.md: "commit format `<pod>: <description>`"
> Personal CLAUDE.md: "no pod prefix in commits"
> → Here the squash-merge pipeline re-adds the prefix, so the team rule survives.
> Check exactly three places for such a mechanism: the CI workflow files, the
> forge's merge-strategy settings, and the repo's hooks. Found in none → report
> the pair as unresolved and ask the user rather than marking OK.

### 2c — Duplication

For each rule or section, check if the same content appears in multiple files.
Near-verbatim means the directives require the same behaviour and differ only
in wording — if the required behaviours differ at all, route it through 2b as
a potential contradiction instead:

- Same file, different section → likely bloat in one of them
- Same content in global preferences AND global CLAUDE.md → one is redundant; flag which to remove
- Same content in project CLAUDE.md AND team AGENTS.md → intentional only if one of them is a symlink to the other or the personal copy says why it repeats the rule; otherwise flag as accidental duplication

Report: source file + section, duplicate file + section, and recommendation (keep in X, remove from Y, or "intentional — leave both").

### 2d — Bloat

Within each file, flag:

- Sections that are pure recaps of other sections in the same file (summary/reminders sections that restate earlier rules verbatim)
- Generic non-actionable advice ("organize them logically", "follow best practices")
- Reference material that could be a single pointer line (e.g. a list of 5 doc subdirectories that could be "docs in `/docs/`")
- Rules that restate the language's or framework's official style-guide default with no project-specific deviation (e.g. "Classes: PascalCase" in Kotlin) — noise a competent reader already assumes
- Procedural checklists whose steps the agent cannot perform. The test: a step is agent-actionable if it maps to a tool invocation or a file edit; flag steps that require physical action, a GUI-only tool, or credentials the agent does not hold

### 2e — Structural health

- Check that each file's symlink chain resolves to a real file (no broken links)
- Check that project preferences are symlinked to the config repo (not standalone copies that can drift)
- Check that global preferences are symlinked to the config repo

## Step 3: Report

Print a structured report:

```
## Agent Config Audit

### Active File Stack
| Logical path | Source | Owner |
|---|---|---|
| ~/.claude/CLAUDE.md | `<config-repo>/<personal-layer>/CLAUDE.md` | personal |
| ... | ... | ... |

### Findings

🔴 Contradiction — [file:section] vs [file:section]
  Both files define commit format but with conflicting rules.
  Recommendation: ...

⚠️ Duplication — [file:section] duplicates [file:section]
  Recommendation: keep in X, remove from Y

📦 Bloat — [file:section]
  "Important Reminders" restates 9 rules already defined earlier in the same file.
  Recommendation: remove section

🚧 Boundary violation — [file:section]
  Personal rule "no pod prefix" found in team AGENTS.md.
  Recommendation: move to personal CLAUDE.md

✅ OK — [N] rules checked, no issues
```

If no issues are found, say so clearly.

## Step 4: Fix (only with `--fix`)

For each finding that has a clear fix:

1. Show the user the proposed edit (before/after diff or description)
2. Ask for approval per finding, or ask "apply all?" for a batch
3. On approval, apply the edit using the Write or Edit tool
4. After all edits, print a summary of what changed

Do **not** apply fixes without explicit approval. Do **not** batch-apply without asking first.

## Flags

Resolve the full stack first (Step 1), then filter by the resolved owner:
`--personal` keeps only files classified personal, `--team` only team-owned —
ownership comes from the classification rule, not from fixed list positions.
`--fix` enables Step 4. `--team` and `--personal` together contradict each
other: stop and ask which scope is meant rather than guessing a union.

## When to STOP

- **Cannot resolve the file stack** (symlinks broken, files missing) → stop and surface the breakage; do not invent file contents.
- **Active project is not managed by a config repo** (no symlinks back to one) → report findings but do not propose fixes that assume one.
- **`--fix` requested but the finding has no unambiguous fix** → describe the trade-off, let the user choose; never auto-pick.
- **Findings touch shared/team files the user does not own** → flag and stop; the user must decide whether to PR upstream.
