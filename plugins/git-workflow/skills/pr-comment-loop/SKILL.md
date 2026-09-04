---
name: pr-comment-loop
description: >
  Use when an active branch has open PRs that may have received new comments since the
  last check. Auto-trigger after any `git push` to a feature branch, after merging a PR
  (its siblings' review threads may have moved), and any time the user asks "is PR N
  ready?" / "what's the status of PRs?" / "manage the open PRs" / "anything to address
  in PR N?" / "review the PR comments". Also fires **before handing over a PR on a
  repo no bot reviews**, where the job is to obtain a review rather than process one.
  Skip if no PRs are open or if the user explicitly says "ignore the comments".
---

# PR comment loop

## Step 0 — when no reviewer is coming

This loop processes findings; a repo no bot reviews produces none, and the
failure is a PR handed over unreviewed. Config is not evidence: hosted reviewers
are usually free for public repos only, and their config file grants nothing
without the app also having access. Ask whether one has ever run there:

```bash
# .user.type is the account's own kind — matching logins against "bot|ai"
# counts a human called chair as a reviewer and misses a bot called sentry
{ gh api "repos/<owner>/<repo>/issues/<n>/comments" --paginate --jq '.[]|select(.user.type=="Bot")|.user.login'
  gh api "repos/<owner>/<repo>/pulls/<n>/reviews"   --paginate --jq '.[]|select(.user.type=="Bot")|.user.login'
} | sort -u
```

Empty means you are the review, so get one from a **fresh context** — the value
is in not having authored the thing. Give it what it cannot discover (what is
vendored, what is deliberate, what is already settled), point it at the PR and
the checked-out branch, tell it to run the claims rather than read them, and
require both an explicit "nothing to report" per category and a verdict. Its
reply is not a GitHub comment, so step 2 will not find it: carry the returned
findings as this round's list, and re-enter at step 3 to verify each against the
source like any bot's. No review obtainable at all → say so and hand the PR
back, rather than merging on your own approval.

**The durable fix is repo-side:** an advisory workflow that reviews each PR and
upserts one sticky comment. Wire it so the model has no write capability (it
writes a file; a plain shell step posts it) and so an empty review warns loudly,
or a green check will mean only that the workflow ran.

## Procedure

For each open PR you have touched in this session — OR all open PRs in the current repo if no explicit list:

1. **Snapshot state**:
   ```bash
   # reviews as well as comments: `--json` returns only what it is asked for,
   # and step 3 reads `.reviews[].body`, where a review's own findings live
   gh pr view <n> --json mergeable,mergeStateStatus,statusCheckRollup,comments,reviews,baseRefName
   ```

2. **Identify NEW comments** since your last reply on that PR. Your last reply is
   the sticky comment, and the upsert in step 6 overwrites whatever selects it,
   silently — so build the selector here, exactly as written, and reuse it there:

   ```bash
   marker='<!-- claude-review-response -->'
   me=$(gh api user -q .login)
   # REST, not `gh pr view` — its objects carry the numeric id and updated_at
   # MY comments whose body STARTS WITH the marker — never `contains`, never the reviewer's
   mine=$(gh api "repos/<owner>/<repo>/issues/<n>/comments" --paginate \
     --jq "[.[] | select(.user.login == \"$me\" and (.body | startswith(\"$marker\")))]")
   ```

   Three traps, all hit for real:

   - **Match the marker with `startswith`, never `contains`.** An automated reviewer that *quotes* your marker — because it is reviewing the very diff that introduced it — matches a `contains` filter, and you overwrite the review.
   - **Exclude the reviewer's own account** from the candidate set, identified by author login, so the filter can only ever select your own comment.
   - **Count the matches here, not in step 6.** Zero is no sticky yet, so every comment is new; one is the sticky; more than one stops the loop and is surfaced to the user. Counting later lets the loop classify, edit and push before it aborts, and overwriting the wrong comment raises no error.

   With exactly one, read the sticky's **last-edit time**, `jq -r '.[0].updated_at'
   <<<"$mine"`: creation time never advances once the sticky is edited in place,
   so the edit time is when you last answered. **A comment created after it is
   new and gets a row this round; one created before it was answered already.**

3. **Verify each finding against the source, then classify it.** Start by
   dropping the ones that are not current: a comment whose `.line` is `null` is
   pinned to a commit the branch has moved past, and on a branch that already
   answered a round, most of those were fixed by the commits that answered it.

   ```bash
   gh api "repos/<owner>/<repo>/pulls/<n>/comments" \
     --jq '.[] | select(.subject_type == "line" and .line == null)
           | {id, path, body, diff_hunk,
              was: .original_line, from: .original_start_line,
              at: .original_commit_id}'
   ```

   Two things that projection is doing deliberately. It keeps what verifying a
   finding needs — the id to reply to it, the body and `diff_hunk` to read what
   it actually said, the full commit id rather than a prefix — because a
   dismissal you cannot re-read is indistinguishable from one you never made.
   And it pins the filter to `subject_type == "line"`, since a file-level
   comment is attached to a whole file rather than a line and is current no
   matter what its line field says. GitHub reports `line: 1` for those today
   (checked by posting one and reading it back), so `.line == null` alone does
   not currently catch them; the guard is there so that a change in that
   behaviour cannot silently turn a live finding into a dismissed one.

   Stale means the line moved, not that the defect is gone, so read the current
   file before dismissing one — but this routinely turns an alarming count into
   none, and re-fixing what is already fixed is how a round produces a diff that
   changes nothing.

   Then, for what remains, open the cited `file:line` in the actual source. Cold-read reviewers see the diff without surrounding context and are confidently wrong often enough that applying findings unchecked introduces bugs — the classic misses: a "missing" guard that exists just outside the hunk, a demanded convention the repo doesn't have, a finding re-raised rounds after it was applied. A finding that does not survive that check is 🚫 Skipped, never silenced — the step 6 table owns the rationale rules.

   Then parse the comment body (`.comments[].body` and `.reviews[].body` from the JSON above) for emoji headings `🔴 Critical`, `🟡 Should fix`, `🟢 Nice to have`; a finding that is pure praise or explicitly requires no action classifies as 💬 Acknowledgement. If the reviewer doesn't use that emoji convention, split the comment into its distinct findings yourself and classify each by the same rules — praise is still 💬, everything actionable defaults to 🟡 — marking each classification as assumed in the reply table so the user can re-grade.

   | Severity | Default action | Rule |
   |---|---|---|
   | 🔴 Critical | Apply | The one exception: paths cited fall outside `gh pr diff <n> --name-only` — then ⏳ Defer with a follow-up issue link |
   | 🟡 Should fix | Apply | Skip if the finding is a false positive (cite the contradicting code / spec line) or out of scope — the fix would touch files absent from `gh pr diff <n> --name-only` (cite which) |
   | 🟢 Nice to have | Apply if diff ≤ 10 lines AND ≤ 1 file | Otherwise defer with a follow-up issue link |
   | 💬 Acknowledgement | No code action | Reference in the reply table only |

4. **Apply fixes** via a single commit per PR with a body that:
   - References the AI review's structure (numbered findings)
   - Names the non-applied findings ("🚫 Skipped #N") — the reply table in
     step 6 carries the reasons

5. **Push + verify** (skip both steps 4–5 when no finding produced a code
   change — the reply in step 6 still goes out, with its `Pushed as` line
   replaced by "No code change this round"):
   ```bash
   git push
   gh pr view <n> --json mergeable,mergeStateStatus
   # confirm CLEAN before reporting back
   ```

6. **Post a reply comment on the PR.** The audit trail of "comment seen, classified, addressed" must live on GitHub — a reply in the Claude session does NOT count. Use sticky-comment style (`<!-- claude-review-response -->` marker → upsert) so re-runs don't spam the PR — **one comment per PR, edited in place across rounds, never a new one each round.**

   ### Posting it

   Upsert against `$mine` from step 2. Re-run that assignment first if the shell
   has been replaced since — the cardinality rule is the same, and a `$mine` that
   is empty because the variable was never set posts a duplicate rather than
   editing in place.

   ```bash
   case "$(jq length <<<"$mine")" in
     0) gh pr comment <n> --body-file reply.md ;;
     1) gh api -X PATCH "repos/<owner>/<repo>/issues/comments/$(jq -r '.[0].id' <<<"$mine")" -F body=@reply.md ;;
     *) echo "more than one sticky match — refusing to patch" >&2; exit 1 ;;
   esac
   ```

   The marker is machine-written — never hand-type it into a comment.

   ### Verdict vocabulary — use these labels EXACTLY

   | Verdict | When to use | Rationale required? |
   |---|---|---|
   | ✅ **Applied** | The fix landed in the same push. Cite the file + line. | No (action column shows the change) |
   | 🚫 **Skipped** | The finding will NOT be addressed — neither now nor later. | YES — one-line reason (false positive, out of scope, intentional design, etc.) |
   | ⏳ **Deferred** | The fix is real but not landing in this PR. | YES — link the follow-up issue / PR / TODO marker |
   | 💬 **Acknowledged** | Praise / "what looks good" notes from the reviewer. No action expected. | No |



   ### Template

   ```markdown
   <!-- claude-review-response -->
   ## ✏️ AI-review response (PR #N)

   | Finding | Verdict | Action / rationale |
   |---|---|---|
   | 🟡 #1 <short title> | ✅ Applied | <file:line + one-line summary> |
   | 🟡 #2 <short title> | 🚫 Skipped | <one-line reason — false positive / scope / intentional> |
   | 🟢 #3 <short title> | ⏳ Deferred | <follow-up reference> |
   | 💬 #4 <short title> | 💬 Acknowledged | — |

   Pushed as `<sha>`.
   ```

   Write the body to `reply.md` and post it with the upsert above, never with a bare `gh pr comment`: that creates a second comment every round, which is the thing this whole step exists to prevent. Even when every finding is 🚫 Skipped with no code change, still post the reply.

   ### Recovering a clobbered comment

   If the wrong comment is overwritten anyway, GitHub retains every prior
   body: query `userContentEdits` via GraphQL (REST does not expose it) —
   both ids come off the same REST object you clobbered (`.node_id`, `.id`):

   ```bash
   gh api graphql -f query='query { node(id: "<node_id>") {
     ... on IssueComment {
       userContentEdits(first: 20) { nodes { editedAt editor { login } diff } }
   } } }'
   ```

   Take the newest `diff` whose `editor` is the original author, save it as
   the body, restore with a REST PATCH, and post your own reply as a
   **separate** comment:

   ```bash
   gh api -X PATCH "repos/<owner>/<repo>/issues/comments/<id>" -F body=@restored.md
   ```

7. **Report back to the user** with a single line per PR:
   ```
   PR #N: <m> findings addressed, <k> skip-justified, reply posted, <state>
   ```

## When to STOP and ask

- `gh` is unauthenticated, or posting/patching the comment is refused — stop
  and hand the user the prepared reply body rather than retrying blind.
- An 🔴 finding's fix is non-trivial AND ambiguous (would require a design call).
- A finding contradicts an earlier decision in the session — surface the contradiction before re-litigating.
- All CI checks are red and root cause isn't obvious — don't push speculative fixes.
- A check that was green in the previous round's step 1 snapshot is red in this
  one — your own fix caused it; surface it before continuing.
- A fix you applied deletes or skips a test — say so and stop, whatever the
  finding claimed. A reviewer asking for less coverage is a finding to argue
  with, not to apply.
- Never close or merge the PR from this skill — that is always the user's call.
