---
name: rescue-a-shared-checkout
description: >
  Use when a working tree you do not exclusively own carries uncommitted changes
  somebody else wrote — a second agent session, a colleague's machine, a
  long-lived VM, a tool that wrote into the tree behind you. Fires on "whose
  changes are these", "the tree is dirty and it isn't mine", "sort out the
  pending changes", and before cutting a branch from a tree whose dirt you did
  not create. Do NOT fire for your own uncommitted work, or for a tree you are
  certain nothing else writes to.
---

# Rescue a shared checkout

Uncommitted work in a tree with more than one writer is the least safe state a
repository has. Nothing records who wrote it, nothing preserves it, and the next
branch cut from that tree carries it by accident. Both obvious moves are wrong:
discarding it destroys work nobody can recover, and committing it all lands
half-written edits under your name.

The job is separating what is already safe from what is genuinely at risk. Most
of a shared tree's dirt is neither.

## Procedure

### 1. Classify every dirty path before touching any of it

A path is dirty for three reasons and only one needs rescuing. Compare against
the branch you would land on, not local `HEAD`: a checkout behind its remote
shows already-merged work as new.

```bash
REMOTE=${REMOTE:-origin}
BASE=${BASE:-develop}   # the branch this tree's work would land on

# A failed fetch leaves a stale ref that still resolves, so the loop would
# answer confidently against the wrong commit. Stop instead.
git fetch "$REMOTE" --quiet || { echo "fetch failed; not classifying against a stale ref"; exit 1; }
git rev-parse --verify --quiet "$REMOTE/$BASE^{commit}" >/dev/null ||
  { echo "no such branch: $REMOTE/$BASE"; exit 1; }

# -z, because the default format QUOTES a path containing a space or a quote and
# every git call downstream then takes the quotes literally. --untracked-files=all,
# because the default collapses an untracked directory into one record that is not
# a file. Under -z a rename emits the new path, then its source as the next record.
git status --porcelain=v1 -z --untracked-files=all |
while IFS= read -r -d "" rec; do
  st=${rec:0:2} path=${rec:3}          # XY, a space, then the path
  case "$st" in
    R*|C*) IFS= read -r -d "" from; echo "AHEAD  $path (was $from)"; continue ;;
    "??")
      # An untracked path is not in the index, so `git diff` cannot answer for it.
      if git cat-file -e "$REMOTE/$BASE:$path" 2>/dev/null &&
         git show "$REMOTE/$BASE:$path" | diff -q - "$path" >/dev/null
        then echo "LANDED $path"; else echo "AHEAD  $path"; fi ;;
    *D*)  echo "AHEAD  $path (deleted)" ;;   # a deletion is work; `cp` cannot carry it
    *)    if git diff --quiet "$REMOTE/$BASE" -- "$path"
            then echo "LANDED $path"   # identical to the branch; discarding loses nothing
            else echo "AHEAD  $path"
          fi ;;
  esac
done
```

Run it in `bash`: in some shells the piped loop body loses its environment and
every `git` call fails, which reads as a clean tree.

**The untracked branch is not optional.** `git diff` compares the index to a
commit, and an untracked path is in neither, so a single-branch version answers
from an error rather than a comparison and inverts both untracked cases. Measured
on a fixture with one untracked file already on the branch and one genuinely new:

| path | truth | `git diff` alone | with the untracked branch |
|---|---|---|---|
| untracked, already on the branch | LANDED | `AHEAD` | `LANDED` |
| untracked, genuinely new | AHEAD | `LANDED` | `AHEAD` |
| tracked, matches the branch | LANDED | `LANDED` | `LANDED` |
| tracked, differs | AHEAD | `AHEAD` | `AHEAD` |

`LANDED` on a genuinely new file is the destructive direction: it is the
instruction to discard the one thing this procedure exists to save.

Expect most of the list to be `LANDED`. Three separate rescues each found that
roughly half the dirty paths were work already merged, showing as modified only
because the checkout had not been fast-forwarded.

### 2. Find out whether the writer has stopped

Rescuing a file mid-edit lands half a thought and, worse, the writer's next save
silently reverts your commit.

```bash
stat -f '%Sm %N' <paths>   # BSD/macOS
stat -c '%y %n' <paths>    # GNU
date
```

Minutes-old timestamps mean someone is still working: say so and stop. The
converse does not hold. **An old timestamp is evidence of nothing having been
written, not of nobody writing** — a paused editor, a session waiting on a
review, a job between runs all look identical to a finished one, and none of
these checks can see a writer that resumes a second later. Treat them as
advisory, say in the pull request which of them you ran, and where a writer can
be asked, ask instead. For a second opinion, ask who holds the files open:

```bash
lsof +D <dir> 2>/dev/null | awk 'NR>1 {print $1, $NF}' | sort -u
```

Cluster the timestamps too — a group of files sharing one timestamp to the
second was written by a tool in one sweep, not typed by a person.

### 3. Copy into a worktree cut from the remote branch

Never commit from the shared tree. Committing there stages files the other writer
is still holding, and a branch cut from it inherits every unrelated edit.

First check the tree is not carrying commits of its own. A worktree cut from
the remote branch starts without them, and nothing later in this procedure
would notice:

```bash
git log --oneline "$REMOTE/$BASE..HEAD"    # empty, or stop and handle these first
```

Then carry the tracked changes as a **patch**, not as copies. `cp` moves file
contents, and the classification above emits paths whose change is not content:
a deletion, a rename, a mode bit. `git apply` reproduces all of them, and
`--binary` keeps a changed image or fixture intact:

```bash
git worktree add "$DEST" -b <branch> "$REMOTE/$BASE"
git diff --binary "$REMOTE/$BASE" -- <tracked AHEAD paths> | git -C "$DEST" apply --binary --index
```

Untracked paths are in no diff, so they are copied, with their directories
created and every path quoted:

```bash
while IFS= read -r path; do
  mkdir -p "$DEST/$(dirname "$path")" && cp "$path" "$DEST/$path"
done < untracked-ahead.txt
```

### 4. Prove the copy is faithful

```bash
diff -q <source> <copy> || echo "MISMATCH"
```

Cheap, and it catches an editor that reflowed on save or a copy that silently
truncated. Byte-identical or start again.

### 5. Re-check the source before you open anything

Between the copy and the push, the writer may have moved. Re-run step 4: an
unchanged source means the branch captures everything, and that sentence belongs
in the pull request rather than being assumed.

### 6. Land the rescue branch from the worktree, never from the shared tree

```bash
git -C "$DEST" add -A && git -C "$DEST" commit && git -C "$DEST" push -u "$REMOTE" HEAD
gh pr create --base "$BASE" --head <branch>
```

### 7. Attribute honestly, and mark what you cannot verify

The claims in rescued work were made by someone with context you do not have.
Land them as reported, and put the limit in the pull request as an unticked box,
where an unticked box is the point rather than an omission:

```markdown
- [ ] The claims here are not independently reproduced. They come from another
      session's work in <where> and are recorded as it reported them.
```

A rescued claim asserted as your own finding is worse than an unrescued file.

### 8. Only then discard, and re-classify first

After the branch merges, the shared tree's copies are usually **stale**, not
ahead: review findings will have improved them on the branch. Stale and ahead
look identical to `git status`, so run step 1 again against the updated branch
before discarding anything, and check the direction:

Ask what kind of file it is first. `diff` answers a binary difference with one
line about the files, so counting `<` and `>` returns zero for both and reads
exactly like "identical" — the answer that authorises the discard:

```bash
if [ "$(git diff --numstat "$REMOTE/$BASE" -- "$path" | cut -f1)" = "-" ]; then
  echo "BINARY $path — stop; a line count cannot compare these"
else
  diff <(cat "$path") <(git show "$REMOTE/$BASE:$path") | grep -c '^>'   # branch adds
  diff <(cat "$path") <(git show "$REMOTE/$BASE:$path") | grep -c '^<'   # branch drops
fi
```

A branch that only adds supersedes the copy. A branch that drops lines the copy
still has is not a superset, and discarding loses them.

## Sharp edges

- **A file differing from the branch by one line may be your own fix.** Copying
  it blindly reverts that line, and the revert is invisible in a diff that shows
  only additions. Read every one-line difference before copying.
- **Tools write into shared trees too.** A reviewer or agent that runs
  `git checkout <ref> -- .` leaves the tree carrying that ref's content, which
  looks exactly like the other writer's work. The tell is the timestamp cluster
  from step 2.
- **`git checkout -- .` and `git clean -fd` are unrecoverable here.** Neither
  distinguishes the three cases in step 1. Classify first, always.
- **A fast-forward refuses while the shared files are modified**, so the tree
  cannot be brought up to date until the rescue lands. That refusal is the safety
  feature, not an obstacle to work around.

## When to STOP

- **The writer is still writing.** Timestamps within minutes of now: report what
  you found and hand it back. Their session holds the context that makes the work
  reviewable.
- **A dirty file is half-written** — a truncated sentence, an unclosed block, a
  test that does not parse. Landing it commits a draft under your name.
- **Everything classifies as LANDED.** There is nothing to rescue; fast-forward
  and say so in one line.
- **The work belongs to someone else's branch or merge.** Report it; do not
  adopt commits whose history you were not asked to touch.
