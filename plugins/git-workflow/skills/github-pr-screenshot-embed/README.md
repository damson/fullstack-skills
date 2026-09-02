# github-pr-screenshot-embed

Makes an image in a GitHub PR description or comment actually render for
reviewers on a **private** repo. The failure is silent and one-sided: pick the
wrong image host and every reviewer sees a broken-image icon while the link
looks fine to you, because your browser is already authenticated. The rule the
skill enforces: `github.com/<owner>/<repo>/raw/<sha>/<path>`, pinned to a
commit SHA.

Read [SKILL.md](SKILL.md) for the rule and its verification. This file is what
it does and how to reach it.

## Using it

- "the screenshot is a broken image in the PR"
- "the image doesn't render for reviewers"
- "add a before/after image to the PR"
- a `raw.githubusercontent.com` link showing as broken

It skips GitLab MRs — GitLab rewrites uploaded paths differently and needs its
own upload step.

## Example

A before/after pair needs to go into a private repo's PR body. The skill:

1. Commits both images into the PR branch (e.g. `docs/screenshots/`) and takes
   the commit SHA with `git rev-parse HEAD`.
2. Builds the embed with the one host that works:

   ```markdown
   | Before | After |
   |---|---|
   | ![before](https://github.com/OWNER/REPO/raw/<sha>/docs/screenshots/before.png) | ![after](https://github.com/OWNER/REPO/raw/<sha>/docs/screenshots/after.png) |
   ```

3. Verifies with runnable checks — the blob exists at the pinned SHA, and no wrong-host URL survived in the PR body. A
   broken image there means the host is wrong, not the file.

Two rules carry all the weight:

- **Never `raw.githubusercontent.com` on a private repo.** That host is
  token-authenticated only and never receives browser cookies — the embed is
  broken for every reader even though the URL resolves for you.
- **Pin the SHA, never the branch.** A squash-merge deletes the branch and
  404s every branch-pinned URL forever; the head commit stays reachable via
  `refs/pull/<n>/head`, so a SHA-pinned embed survives the merge.

One dead end it saves you from: drag-and-drop attachments cannot be scripted —
the upload endpoint 422s without a real browser session — so committing the
image and referencing it by SHA is the way.

## Related

- `capture-pr-screenshots` — produces the images this skill embeds.
- `coverage-pr-comment` — same audience problem, different artefact: making a
  PR comment carry information that actually renders.
