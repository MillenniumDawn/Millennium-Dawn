#!/usr/bin/env bash
# Bring one branch from the archive onto the new history, without the old history.
# For instructions: tools/migrate_branch.sh --help
set -euo pipefail

ARCHIVE=${ARCHIVE:-}
ARCHIVE_URL=https://github.com/MillenniumDawn/millennium-dawn-archive
OLD_MARKER=56b0cfc609b39d4d0d4666ec20b9fe0fb3008069
REMOTE=migrate-archive
MAP=${MAP:-}
usage="usage: tools/migrate_branch.sh BRANCH [--push]"
show_help() {
  cat <<EOF
$usage

Move one branch from millennium-dawn-archive onto the new main history.
The script replays the branch's own commits on the matching new commit. The old
history does not come along, and merge commits inside the branch are flattened.

BEFORE YOU START
  1. Use a clone of Millennium-Dawn made after the history cut.
  2. Switch to main and commit or stash your changes.
  3. Optional: keep a full clone of the archive next to the main checkout:

       parent-folder/
         Millennium-Dawn/
         millennium-dawn-archive/

     The script finds it from any worktree, reads it directly and never writes
     to it. The archive is read-only on GitHub, so the clone needs no updates.
     Without one, the script fetches what it needs from GitHub. To get one
     (about 10 GB), run this from the main checkout:
       git clone $ARCHIVE_URL ../millennium-dawn-archive

FIND THE BRANCH NAME
  With a local archive, run this from the main checkout and drop the origin/
  prefix from the names it lists:
    git -C ../millennium-dawn-archive branch -r
  Without one:
    git ls-remote --heads $ARCHIVE_URL

USAGE
  tools/migrate_branch.sh BRANCH           migrate, then push it yourself
  tools/migrate_branch.sh BRANCH --push    migrate, push if the files match
  tools/migrate_branch.sh --help           show this help

SETTINGS
  Put these in front of the command, as in: MAP=path tools/migrate_branch.sh BRANCH

  ARCHIVE=path-or-url  Use another archive. A path must be a full clone.
  MAP=path             The commit-map file that git filter-repo wrote during the
                       cut. Needed if the branch forked from main before 2026.
  SKIP_FETCH=1         Do not fetch origin/main first. With a local archive,
                       this works offline.

WHAT CAN HAPPEN
  Files match
    The local branch is created and you are back where you started. It is
    pushed only with --push.

  Files differ
    You are left on the new branch and nothing is pushed. This usually means an
    edit made inside a merge commit was lost. The script prints the commands to
    compare, restore and push.

  Conflict
    The rebase pauses and the script prints numbered steps to finish it.
    To give up at any point before it finishes:
      git rebase --abort && git switch main

IF THE PUSH IS REJECTED
  The branch is probably on origin already because someone migrated it.
  Compare before doing anything else, and do not force push over it:
    git fetch origin BRANCH
    git diff --stat BRANCH origin/BRANCH
EOF
}
die() { echo "error: $*" >&2; exit 1; }
assert_new_history() {
  local message=$1 commits
  shift
  commits=$(git rev-list "$@") || die "cannot read the history of $*"
  if [[ $commits == *"$OLD_MARKER"* ]]; then die "$message"; fi
}
drop_archive() {
  git remote remove "$REMOTE" 2>/dev/null || true
  git update-ref -d refs/migrate/branch
  git update-ref -d refs/migrate/main
}
copy_from_archive() {
  local pack_dir
  pack_dir=$(git rev-parse --git-path objects/pack)
  # A rebase walks every old commit, but reads files only from the replayed commits and their parents.
  {
    git rev-list "$tip"
    {
      echo "$base"
      echo "$tip"
      git rev-list --no-merges --parents "$base..$tip" | tr ' ' '\n'
    } | git rev-list --objects --no-object-names --no-walk --stdin
  } | env -u GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NO_LAZY_FETCH=1 git cat-file --batch-check |
    awk '$2 == "missing" {print $1}' |
    git pack-objects -q --non-empty --window=0 "$pack_dir/pack" >/dev/null
}
rebase_dir() {
  local name dir
  for name in rebase-merge rebase-apply; do
    dir=$(git rev-parse --git-path "$name")
    if [ -d "$dir" ]; then echo "$dir"; fi
  done
}
make_abort_safe() {
  local dir
  dir=$(rebase_dir)
  # A plain --abort would check out the old history, whose older trees are not all here.
  if [ -n "$dir" ]; then echo "$start_commit" >"$dir/orig-head"; fi
}
review_help() {
  cat <<EOF
Compare with the archive branch:
  git diff --stat HEAD $want
No output means the files match, so go straight to the push.

If the branch forked in 2026 or later, any difference is a lost edit. To restore all:
  git restore --source=$want --staged --worktree :/
  git commit -m 'Restore merge edits from the archive'

If it forked before 2026, the cut itself removed files. Restore only what you need:
  git restore --source=$want --staged --worktree -- PATH
  git commit -m 'Restore merge edits from the archive'

Push, then go back to $start:
  git push -u origin $branch && git switch $start
EOF
}
conflict_help() {
  cat <<EOF

Conflict. The rebase is paused.

1. Fix the files that git status lists as unmerged.
   To see how a file ends up on the archive branch:
     git show $tip:PATH
2. Continue. Repeat 1 and 2 until the rebase finishes:
     git add -A && git rebase --continue
3. Create the branch:
     git switch -c $branch
4. Check that the old history is gone. This must print 0:
     git rev-list HEAD | grep -c $OLD_MARKER
5. Review and push, as below.

To give up before step 3:
  git rebase --abort && git switch $start

EOF
  review_help
}

case "${1:-}" in
  -h | --help)
    show_help
    exit 0
    ;;
  "" | -*) die "$usage (--help for instructions)" ;;
esac
branch=$1
push=${2:-}
[ -z "$push" ] || [ "$push" = "--push" ] || die "$usage (--help for instructions)"

git rev-parse --git-dir >/dev/null || die "run this inside a Millennium-Dawn clone"
[ -z "$(rebase_dir)" ] || die "a rebase is in progress. Finish it with git rebase --continue, or give up with git rebase --abort."
dirty=$(git status --porcelain) || die "cannot read the working tree"
[ -z "$dirty" ] || die "working tree is not clean. See git status, then commit or stash."
start=$(git symbolic-ref -q --short HEAD) || die "HEAD is detached. If a migration just finished, create its branch with git switch -c BRANCH. Otherwise run git switch main."
start_commit=$(git rev-parse HEAD)
if git show-ref --verify --quiet "refs/heads/$branch"; then
  die "local branch $branch already exists. If it is a failed attempt with nothing you need, switch to main, delete it with git branch -D $branch and run this again."
fi
[ -n "${SKIP_FETCH:-}" ] || git fetch -q origin main
assert_new_history "this clone is on the old history. Make a new clone of Millennium-Dawn and run this there." HEAD origin/main --branches --tags --remotes

if [ -z "$ARCHIVE" ]; then
  common=$(git rev-parse --path-format=absolute --git-common-dir)
  ARCHIVE=$(dirname "$(dirname "$common")")/millennium-dawn-archive
  [ -d "$ARCHIVE" ] || ARCHIVE=$ARCHIVE_URL
fi
echo "archive: $ARCHIVE"

borrowed=""
tip=refs/migrate/branch
old_main=refs/migrate/main
if [ -d "$ARCHIVE" ]; then
  # A clone has the archive's branches only as origin/*.
  tip=$(git -C "$ARCHIVE" rev-parse --verify -q "refs/remotes/origin/$branch") ||
    die "no origin/$branch in $ARCHIVE. List the branches with: git -C '$ARCHIVE' branch -r"
  old_main=$(git -C "$ARCHIVE" rev-parse --verify -q refs/remotes/origin/main) ||
    die "no origin/main in $ARCHIVE. It must be a full clone of $ARCHIVE_URL"
  borrowed=$(git -C "$ARCHIVE" rev-parse --path-format=absolute --git-path objects)
  export GIT_ALTERNATE_OBJECT_DIRECTORIES=$borrowed
elif [ -z "${SKIP_FETCH:-}" ]; then
  trap drop_archive EXIT
  git remote remove "$REMOTE" 2>/dev/null || true
  git remote add --no-tags "$REMOTE" "$ARCHIVE"
  git fetch -q --filter=blob:none --no-tags "$REMOTE" \
    "+refs/heads/$branch:refs/migrate/branch" "+refs/heads/main:refs/migrate/main" ||
    die "cannot fetch $branch from $ARCHIVE. List the branches with: git ls-remote --heads '$ARCHIVE'"
fi

tip=$(git rev-parse "$tip^{commit}")
want=$(git rev-parse "$tip^{tree}")
base=$(git merge-base "$tip" "$old_main")
new=""
if [ -n "$MAP" ]; then new=$(awk -v m="$base" '$1==m {print $2}' "$MAP"); fi
if [ -z "$new" ]; then
  tree=$(git rev-parse "$base^{tree}")
  new=$(git log origin/main --format='%H %T' | awk -v t="$tree" '$2==t && !found {print $1; found=1}')
fi
[ -n "$new" ] || die "no matching commit on the new main for $base. The branch probably forked before 2026. Run again with MAP=/path/to/commit-map (see --help)."
git merge-base --is-ancestor "$new" origin/main || die "$new is not on the new main"

echo "branch forked from main at: $(git log -1 --format='%cs %s' "$base")"
echo "commits to replay: $(git rev-list --count --no-merges "$base..$tip")"

if [ -n "$borrowed" ]; then
  copy_from_archive
  # Git does not write objects it can borrow, so stop borrowing before the rebase.
  unset GIT_ALTERNATE_OBJECT_DIRECTORIES
else
  # The archive remote is removed before the rebase, so fetch the blobs it needs now.
  {
    git log --no-merges --format= --raw --no-abbrev --no-renames "$base..$tip"
    git diff-tree -r "$base" "$tip"
  } | awk '/^:/ {if ($3 !~ /^0+$/) print $3; if ($4 !~ /^0+$/) print $4}' |
    git pack-objects -q --window=0 --stdout >/dev/null
  drop_archive
fi

# Also covers Ctrl-C during the rebase.
trap make_abort_safe EXIT
if ! git rebase --onto "$new" "$base" "$tip"; then
  [ -n "$(rebase_dir)" ] || die "the rebase did not start. See the git error above."
  conflict_help
  exit 1
fi

assert_new_history "result still contains the old history. Do not push." HEAD
git switch -q -c "$branch"
echo "ok: branch is on the new history"

got=$(git rev-parse "HEAD^{tree}")
if [ "$got" != "$want" ]; then
  echo "note: files differ from the archive branch in $(git diff-tree -r --name-only "$got" "$want" | wc -l) paths. Not pushed. You are on $branch."
  echo
  review_help
  [ "$push" != "--push" ] || die "refusing to push files that differ from the archive branch"
  exit 0
fi
echo "ok: files are identical to the archive branch"
# The migrated branch may predate this script.
git switch -q "$start"

if [ "$push" = "--push" ]; then
  git push -u origin "$branch" || die "push failed. The local branch $branch is ready. If origin rejected it, see --help before retrying."
else
  echo "Not pushed. When ready: git push -u origin $branch"
fi
