# pre-publication-sweep

Sweeps a repository (working tree, every blob in every commit on every branch,
commit metadata, and the remote itself) for the names, emails and credential
prefixes that must not go public, before the repo crosses a line it cannot come
back from. The failure it prevents is the confident false clean: publishing is
a write with no undo, because caches, forks and mirrors outlive a deletion.

Read [SKILL.md](SKILL.md) for the procedure. This file is when to reach for it
and what its report looks like.

## Using it

Ask for it in any of these shapes:

- "make it public" / "open source this"
- "check nothing confidential leaks"
- pushing an extract or a repo to any host others can read

It deliberately does **not** fire:

- on a repo that is **already public**: its history is already out, and the
  task is exposure response, not a sweep
- for content that never leaves the machine

Two of its rules do the real work. The term list is built from the people
involved: the owner is asked what is sensitive, because you cannot grep for a
name you were never told. And the sweep re-verifies on the **remote**, never
only a local clone, which can show clean where the remote is not.

## Example

The deliverable is the list of commands run and their results, never the word
"clean" on its own:

> ```
> grep -rIiE '<terms>' . --exclude-dir=.git            → no matches
> git rev-list --all --remotes | … git grep -iIlE …    → no matches
> git log --all --format='%ae %ce %s' | grep -iE …     → no matches
> gh api 'repos/o/r/commits?sha=develop&per_page=100'  → 1 email, the public one
> gitleaks detect                                      → no leaks found
> ```
>
> Swept for: 2 personal emails, employer name, 2 internal project names,
> `sk-` / `ghp_` / `AKIA` prefixes. All branches enumerated; none over 100
> commits, so no pagination gap.

An empty sweep is evidence only when the reader can see what was swept. On any
hit the skill stops and reports it verbatim: scrubbing is the owner's
decision, because it may mean a history rewrite, which orphans every pin on
the old SHAs.

## Related

- `reversible-bulk-write` (this plugin), the same principle, inverted: that
  skill makes a write undoable; this one exists because publishing never is.
- `bump-vendored-pin` (git-workflow plugin): what a history rewrite does to
  pinned SHAs, from the consumer's side.
