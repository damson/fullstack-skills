# save-before-compact

A pre-compaction gate for long sessions: captures what the session taught into
the right homes (CLAUDE.md / preference files / memory; versioned targets
first), optionally creates the skills the session earned, writes a resume
brief, then stops for you to run `/compact`. The failure it prevents: a long
session's hard-won learnings evaporating because compaction summarised them
away.

Read [SKILL.md](SKILL.md) for the nine-step procedure.

**It never fires unsolicited**, and it never runs `/compact` itself: that last
keypress is always yours.

## Using it

- "save before compact"
- "wrap up and compact"
- "session's too long, compact but keep the takeaways"
- "capture learnings then compact"

It skips thin sessions (fewer than ~15 substantive turns go straight to the
resume brief), defers when a high-stakes operation is in flight (deploy,
mid-merge, incident), and refuses to run on someone else's transcript.

## Example

After a 40-turn debugging session:

1. It lists candidate facts (commands discovered, gotchas, decisions) and
   applies the keep-test: keep only what would prevent a realistic future
   mistake and is not already written down. Weak candidates are dropped:
   a missed one costs nothing, a weak one bloats the file.
2. Each surviving addition is shown as a diff (target file, one-line why, the
   line itself), and **you approve or skip each one**. Nothing is written
   without approval.
3. Applied changes are verified (the repo's skill-structure tests or eval
   command if it ships one, an inline five-dimension rubric otherwise).
4. `skill-opportunity-finder` runs (or, where that plugin is not installed,
   the same pattern scan happens inline and says so); approved skill
   candidates are created *now*, before compaction: authoring a good skill
   needs the live context that compaction discards.
5. A resume brief (Goal · Done · Next actions · Open questions · Key files) is
   written into `.claude/` with a stable `session-resume-latest.md` pointer,
   the ledger is printed, and the skill stops:

   > Learnings saved and verified, resume brief at `.claude/…` — safe to run
   > `/compact` now. I'll read it to pick up.

## Related

- `skill-opportunity-finder`: invoked as step 7 to surface patterns worth a
  new skill.
- `session-retro`, the report-only sibling: it produces signal and applies
  nothing, where this skill applies approved changes before the context is
  lost.
