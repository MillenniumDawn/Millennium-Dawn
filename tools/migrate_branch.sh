#!/usr/bin/env bash
# Bring one branch from the archive onto the new history, without the old history.
# Run inside a clean clone of the main repository made after the cut.
#
# usage: migrate_branch.sh BRANCH [--push]
#        MAP=/path/to/commit-map migrate_branch.sh BRANCH    for a branch that
#        forked from main before 2026
#
# It replays the branch's own commits on top of the matching new commit.
# Merge commits inside the branch are flattened. If that changes the files,
# nothing is pushed.
set -euo pipefail

ARCHIVE=${ARCHIVE:-https://github.com/MillenniumDawn/millennium-dawn-archive}
OLD_MARKER=56b0cfc609b39d4d0d4666ec20b9fe0fb3008069
REMOTE=migrate-archive
MAP=${MAP:-}
usage="usage: migrate_branch.sh BRANCH [--push]"
branch=${1:?$usage}
push=${2:-}
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
review_help() {
  echo "  git diff --stat HEAD $want"
  echo "For a branch that forked in 2026 or later, any difference is a lost edit. To restore:"
  echo "  git restore --source=$want --staged --worktree :/"
  echo "  git commit -m 'Restore merge edits from the archive'"
  echo "Then: git push -u origin $branch && git switch $start"
}

[ -z "$push" ] || [ "$push" = "--push" ] || die "$usage"
dirty=$(git status --porcelain) || die "cannot read the working tree"
[ -z "$dirty" ] || die "working tree is not clean"
start=$(git symbolic-ref -q --short HEAD) || die "HEAD is detached. Finish the last migration or switch to main."
git show-ref --verify --quiet "refs/heads/$branch" && die "local branch $branch already exists"
[ -n "${SKIP_FETCH:-}" ] || git fetch -q origin main
assert_new_history "this clone is on the old history. Re-clone first." HEAD origin/main --branches --tags --remotes

if [ -z "${SKIP_FETCH:-}" ]; then
  trap drop_archive EXIT
  git remote remove "$REMOTE" 2>/dev/null || true
  git remote add --no-tags "$REMOTE" "$ARCHIVE"
  git fetch -q --filter=blob:none --no-tags "$REMOTE" \
    "+refs/heads/$branch:refs/migrate/branch" "+refs/heads/main:refs/migrate/main"
fi

tip=$(git rev-parse "refs/migrate/branch^{commit}")
want=$(git rev-parse "$tip^{tree}")
base=$(git merge-base "$tip" refs/migrate/main)
new=""
if [ -n "$MAP" ]; then new=$(awk -v m="$base" '$1==m {print $2}' "$MAP"); fi
if [ -z "$new" ]; then
  tree=$(git rev-parse "$base^{tree}")
  new=$(git log origin/main --format='%H %T' | awk -v t="$tree" '$2==t && !found {print $1; found=1}')
fi
[ -n "$new" ] || die "no matching commit on the new main for $base. Pass MAP=commit-map."
git merge-base --is-ancestor "$new" origin/main || die "$new is not on the new main"

echo "branch forked from main at: $(git log -1 --format='%cs %s' "$base")"
echo "commits to replay: $(git rev-list --count --no-merges "$base..$tip")"

# The archive remote is removed before the rebase, so fetch the blobs it needs now.
{
  git log --no-merges --format= --raw --no-abbrev --no-renames "$base..$tip"
  git diff-tree -r "$base" "$tip"
} | awk '/^:/ {if ($3 !~ /^0+$/) print $3; if ($4 !~ /^0+$/) print $4}' |
  git pack-objects -q --window=0 --stdout >/dev/null
drop_archive
trap - EXIT

if ! git rebase --onto "$new" "$base" "$tip"; then
  if [ ! -d "$(git rev-parse --git-path rebase-merge)" ] && [ ! -d "$(git rev-parse --git-path rebase-apply)" ]; then
    die "the rebase did not start. See the git error above."
  fi
  echo
  echo "Conflict. Fix the files, then: git add -A && git rebase --continue"
  echo "To give up: git rebase --quit && git switch --discard-changes $start"
  echo "When it finishes: git switch -c $branch, then run the checks by hand:"
  echo "  git rev-list HEAD | grep -c $OLD_MARKER     (must print 0)"
  review_help
  exit 1
fi

assert_new_history "result still contains the old history. Do not push." HEAD
git switch -q -c "$branch"
echo "ok: branch is on the new history"

got=$(git rev-parse "HEAD^{tree}")
if [ "$got" != "$want" ]; then
  echo "note: files differ from the archive branch in $(git diff-tree -r --name-only "$got" "$want" | wc -l) paths. Not pushed. Review:"
  review_help
  [ "$push" != "--push" ] || die "refusing to push files that differ from the archive branch"
  exit 0
fi
echo "ok: files are identical to the archive branch"
# The migrated branch may predate this script.
git switch -q "$start"

if [ "$push" = "--push" ]; then
  git push -u origin "$branch"
else
  echo "Not pushed. When ready: git push -u origin $branch"
fi
