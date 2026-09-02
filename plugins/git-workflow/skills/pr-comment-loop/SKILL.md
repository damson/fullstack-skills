---
name: pr-comment-loop
description: >
  Use when an active branch has open PRs that may have received new comments since the
  last check. Auto-trigger after any `git push` to a feature branch, after merging a PR
  (its siblings' review threads may have moved), and any time the user asks "is PR N
  ready?" / "what's the status of PRs?" / "manage the open PRs" / "anything to address
  in PR N?" / "review the PR comments". Skip if no PRs are open or if the user explicitly
  says "ignore the comments".
---

# PR comment loop

## Procedure

For each open PR you have touched in this session — OR all open PRs in the current repo if no explicit list:

1. **Snapshot state**:
   ```bash
   gh pr view <n> --json mergeable,mergeStateStatus,statusCheckRollup,comments,baseRefName
   ```

2. **Identify NEW comments** since your last reply on that PR: run the sticky-comment selector (defined once, in step 6 where it is also used to post) and compare each comment's `createdAt` against the sticky's **last-edit time**, `jq -r '.[0].updated_at' <<<"$mine"` — the selector's `select()` keeps whole REST comment objects, and creation time never advances once the sticky is edited in place. No sticky yet → every comment is new.

3. **Verify each finding against the source, then classify it.** Before acting on a finding, open the cited `file:line` in the actual source. Cold-read reviewers see the diff without surrounding context and are confidently wrong often enough that applying findings unchecked introduces bugs — the classic misses: a "missing" guard that exists just outside the hunk, a demanded convention the repo doesn't have, a finding re-raised rounds after it was applied. A finding that does not survive that check gets a 🚫 Skipped row (verdict vocabulary in step 6) citing the contradicting line — never silence.

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

   ### Finding the sticky comment safely

   The upsert overwrites whatever it selects, and does so silently — so the selector must be exact. Three traps, all hit for real:

   - **Match the marker with `startswith`, never `contains`.** An automated reviewer that *quotes* your marker — because it is reviewing the very diff that introduced it — matches a `contains` filter, and you overwrite the review.
   - **Exclude the reviewer's own account** from the candidate set, identified by author login, so the filter can only ever select your own comment.
   - **Count the matches and abort unless exactly one.** Patch the single match; if zero, post fresh; if more than one, stop and surface it. Overwriting the wrong comment raises no error.

   ```bash
   marker='<!-- claude-review-response -->'
   me=$(gh api user -q .login)
   # MY comments whose body STARTS WITH the marker — never `contains`, never the reviewer's
   mine=$(gh pr view <n> --json comments \
     --jq "[.comments[] | select(.author.login == \"$me\" and (.body | startswith(\"$marker\")))]")
   case "$(jq length <<<"$mine")" in
     0) : "post a fresh comment" ;;
     1) : "PATCH that one comment (edit in place)" ;;
     *) : "STOP — more than one match, do not patch" ;;
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

   Post via `gh pr comment <n> --body "$(cat <<'EOF' ... EOF)"`. Even when every finding is 🚫 Skipped with no code change, still post the reply.

   ### Recovering a clobbered comment

   If you do overwrite the wrong comment, GitHub retains every prior body — recover it before anything else. REST does not expose this; GraphQL does:

   ```bash
   gh api graphql -f query='
   { repository(owner:"OWNER", name:"REPO") { pullRequest(number:NN) {
       comments(first:20) { nodes { databaseId
         userContentEdits(first:20) { nodes { editedAt editor { login } diff } } } } } } }'
   ```

   `userContentEdits` returns prior bodies newest-first. Take the last one written by the original author, write it to a file, and restore with `gh api -X PATCH repos/OWNER/REPO/issues/comments/<id> -F body=@restore.md`. Then post your own reply as a **separate** comment.

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
- Test count drops vs the previous push — surface this before continuing.
- Never close or merge the PR from this skill — that is always the user's call.
