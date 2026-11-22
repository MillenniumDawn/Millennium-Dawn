#!/usr/bin/env bash
# Bring one branch from the archive onto the new history, without the old history.
# Run inside a clean clone of the main repository made after the cut.
#
# usage: migrate_branch.sh BRANCH [--push]
#        MAP=/path/to/commit-map migrate_branch.sh BRANCH    for a branch that
#        forked from main before 2026
#
# It replays the branch's own commits on top of the matching new commit.
# Merge commits inside the branch are flattened.
set -euo pipefail

ARCHIVE=${ARCHIVE:-https://github.com/MillenniumDawn/millennium-dawn-archive}
OLD_MARKER=56b0cfc609b39d4d0d4666ec20b9fe0fb3008069
MAP=${MAP:-}
branch=${1:?usage: migrate_branch.sh BRANCH [--push]}
push=${2:-}
die() { echo "error: $*" >&2; exit 1; }
has_old_history() { [ "$(git rev-list "$1" | grep -c "^$OLD_MARKER$" || true)" != 0 ]; }

[ -z "$(git status --porcelain)" ] || die "working tree is not clean"
git show-ref --verify --quiet "refs/heads/$branch" && die "local branch $branch already exists"
if [ -z "${SKIP_FETCH:-}" ]; then
  git fetch -q origin main
  git remote get-url archive >/dev/null 2>&1 || git remote add archive "$ARCHIVE"
  git fetch -q --filter=blob:none --no-tags archive \
    "+refs/heads/$branch:refs/migrate/branch" "+refs/heads/main:refs/migrate/main"
fi
if has_old_history origin/main; then
  die "this clone is on the old history. Re-clone first."
fi

base=$(git merge-base refs/migrate/branch refs/migrate/main)
new=""
if [ -n "$MAP" ]; then new=$(awk -v m="$base" '$1==m {print $2}' "$MAP"); fi
if [ -z "$new" ]; then
  tree=$(git rev-parse "$base^{tree}")
  new=$(git log origin/main --format='%H %T' | awk -v t="$tree" '$2==t && !found {print $1; found=1}')
fi
[ -n "$new" ] || die "no matching commit on the new main for $base. Pass MAP=commit-map."
git merge-base --is-ancestor "$new" origin/main || die "$new is not on the new main"

echo "branch forked from main at: $(git log -1 --format='%cs %s' "$base")"
echo "commits to replay: $(git rev-list --count --no-merges "$base..refs/migrate/branch")"

if ! git rebase --onto "$new" "$base" "refs/migrate/branch^{commit}"; then
  echo
  echo "Conflict. Fix the files, then: git add -A && git rebase --continue"
  echo "When it finishes: git switch -c $branch, then run the checks by hand:"
  echo "  git rev-list HEAD | grep -c $OLD_MARKER     (must print 0)"
  exit 1
fi
git switch -q -c "$branch"

if has_old_history HEAD; then
  die "result still contains the old history. Do not push."
fi
echo "ok: branch is on the new history"
if git diff --quiet HEAD refs/migrate/branch; then
  echo "ok: files are identical to the archive branch"
else
  echo "note: files differ from the archive branch in $(git diff --name-only HEAD refs/migrate/branch | wc -l) paths."
  echo "      Expected for a branch that forked before 2026. Review: git diff --stat HEAD refs/migrate/branch"
fi
git update-ref -d refs/migrate/branch
git update-ref -d refs/migrate/main

if [ "$push" = "--push" ]; then
  git push -u origin "$branch"
else
  echo "Not pushed. When ready: git push -u origin $branch"
fi
