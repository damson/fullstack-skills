# capture-pr-screenshots

Takes a PR that changed a UI page from "the diff touched a route file" to "the
PR body shows a SHA-pinned image": finds the changed surfaces, boots the dev
server with the right auth bypass, captures each page headlessly, rejects
captures that lie (a login form, a blank shell, an unstyled page), and commits
the images so they can be referenced by commit SHA. The failure it prevents is
the UI PR a reviewer must check out and run just to see.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

Fires when a PR changes a UI route file (`page.tsx`, `+page.svelte`, a
`routes/` entry) without a matching screenshot, or on:

- "you forgot the screenshot"
- "capture the screenshot for this PR"
- "no screenshot for the UI"

It skips backend-only PRs. And where the repo documents its own capture
command, it runs that instead — the built-in steps are the fallback for repos
that document nothing.

## Example

A PR edits `app/settings/page.tsx` and has no image. The skill:

1. Diffs against the PR base to list the changed routes, and locates the
   existing screenshots directory to follow its naming.
2. Pre-flights: links the primary worktree's `.env` into this one, and greps
   the code for the auth-bypass variable rather than assuming its name —
   more than one candidate is a stop-and-ask, because guessing which gate the
   page honours is how you capture the login form.
3. Starts the dev server with the bypass exported (not inline — an inline var
   may not reach the child), then reads the port it actually bound from the
   log, with a bounded wait so a server that dies fails loudly instead of
   hanging.
4. Captures with headless Chrome at the viewport the existing screenshots use.
5. Views each PNG before trusting it. A screenshot of the login page is worse
   than none — it looks like evidence.
6. Kills the server it started, by PID — never "whatever holds the port", which
   takes down someone else's server when the port was already busy.
7. Commits the image, then edits the PR body in place to reference it by
   commit SHA.

The URL shape for step 7 — SHA-pinned, `github.com/<owner>/<repo>/raw/...` —
belongs to `github-pr-screenshot-embed`; this skill defers to it.

## Related

- `github-pr-screenshot-embed` — the host rule that makes the committed image
  render for reviewers on a private repo.
- `worktree-bootstrap` — when the capture has to run in a secondary worktree
  that has never been set up.
