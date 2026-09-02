# pr-comment-loop

Closes the loop on PR review comments — AI and human — instead of waiting to be
asked. Every finding is verified against the actual source before it is acted
on, every verdict lands in **one** sticky reply comment on the PR (edited in
place across rounds, never a new comment per round), and no finding is ever
answered with silence. The failure it prevents is the unreadable review thread:
ten pushes, ten bot comments, and findings that were quietly dropped.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

It auto-triggers after any `git push` to a feature branch and after merging a
PR. You can also ask directly:

- "is PR 14 ready?"
- "anything to address in PR 14?"
- "review the comments"
- "what's the status of the PRs?"

It skips when no PRs are open, or when you say "ignore the comments". It never
closes or merges a PR — that stays your call.

## Example

A push lands on PR #14 and an AI reviewer leaves four findings. The skill:

1. Snapshots the PR state and identifies which comments are new since its last
   sticky reply.
2. Opens each cited `file:line` in the source before classifying. Cold-read
   reviewers are confidently wrong often enough that this step regularly kills
   findings — a guard reported missing that already existed six lines above the
   hunk, a changelog demanded in a repo with no changelog.
3. Applies what survives as a single commit, pushes, and confirms the PR is
   back to `CLEAN`.
4. Upserts the reply comment — found by its machine-written
   `<!-- claude-review-response -->` marker, matched with `startswith` (never
   `contains`, which an automated reviewer quoting the marker would also
   match), the reviewer's own account excluded, and the patch aborted unless
   exactly one comment matches:

   | Finding | Verdict | Action / rationale |
   |---|---|---|
   | 🟡 #1 null check | ✅ Applied | `parser.ts:88` — guard added |
   | 🟡 #2 constraint violation | 🚫 Skipped | false positive — value is an array literal, no constraint applies |
   | 🟢 #3 rename suggestion | ⏳ Deferred | follow-up issue #31 |
   | 💬 #4 test coverage praise | 💬 Acknowledged | — |

The four verdicts are the entire vocabulary — "Considered" and "Noted" are
forbidden, because the point of the table is that every row is unambiguous.

The report back is one line per PR:

```
PR #14: 1 finding addressed, 1 skip-justified, 1 deferred, reply posted, CLEAN
```

## Related

- `branch-hygiene` — the post-merge cleanup that often precedes a re-review
  round.
- `coverage-pr-comment` — the same sticky-comment upsert discipline, applied to
  coverage numbers.
- `github-pr-screenshot-embed` — when a reply needs an image that actually
  renders for reviewers on a private repo.
