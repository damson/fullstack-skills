# worktree-bootstrap

Makes a freshly created git worktree actually run. A new worktree shares the
repo's history but none of its machine-local life: `.env` files are gitignored
and absent, `node_modules` / `.venv` / codegen output do not exist yet, and
submodules are unpopulated. The first `dev` or `test` run then fails on a
variable that "works on the other branch". This skill copies the ignored config
from a donor worktree, rebuilds the dependencies for the detected stack, and
proves the result by running something real.

Read [SKILL.md](SKILL.md) for the procedure. This file is what it does and how
to reach it.

## Using it

Fires right after `git worktree add` or `git gtr new`, or on:

- "set up the worktree"
- "the new worktree won't build"
- "missing .env in the worktree"
- "gradle can't find the SDK / local.properties"

It skips when the repo ships its own bootstrap skill (that one knows the extra
credential files and hooks), and when the worktree has already run once.

## Example

A new worktree of a pnpm app dies on startup with a missing env var. The skill:

1. Detects the stack from the lockfile — `pnpm-lock.yaml` → pnpm, so the
   install is `pnpm install`, never `npm install`, which would rewrite the
   lockfile.
2. Finds a donor worktree of the same repo (machine-local config is
   per-machine, not per-branch).
3. Lists the donor's gitignored files — with `--ignored`, because the default
   listing *hides* exactly the files that need to come across:

   ```bash
   git -C "$SOURCE" ls-files --others --ignored --exclude-standard
   ```

   and copies the `.env` / `.env.local` matches into the same relative paths.
   Nothing is ever fabricated: if the donor lacks a file the stack needs, the
   skill stops and asks.
4. Installs dependencies, populates submodules if `.gitmodules` exists, and
   runs any `postinstall` / `generate` / `prisma generate` step the repo
   actually declares.
5. Verifies with the cheapest command that exercises real config — `pnpm
   typecheck`, or `./gradlew help -q` on Android, which proves
   `local.properties` resolves. A green install is not proof; the app reading
   its env is.

## Related

- `capture-pr-screenshots` — its pre-flight linking of env files into a
  secondary worktree is this skill's problem in miniature.
- `branch-hygiene` — creates the temporary worktrees this skill may then need
  to make runnable.
