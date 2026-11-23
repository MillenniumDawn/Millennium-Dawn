#!/usr/bin/env bash
# Replay one archive branch onto the new history, keeping its merges.
# For instructions: tools/migrate_branch.sh --help
set -euo pipefail

ARCHIVE=${ARCHIVE:-}
ARCHIVE_URL=https://github.com/MillenniumDawn/millennium-dawn-archive
OLD_MARKER=56b0cfc609b39d4d0d4666ec20b9fe0fb3008069
MAP=${MAP:-}
usage="usage: tools/migrate_branch.sh BRANCH [--push]"
show_help() {
  cat <<EOF
$usage

Move one branch from millennium-dawn-archive onto the new main history.
The script replays the branch's own commits and merges on top of the matching
new main commits, so conflict resolutions inside merges are kept. The old
history does not come along. Commit signatures are lost, because a rewritten
parent cannot keep them.

BEFORE YOU START
  Keep a full clone of the archive next to the main checkout. The script reads
  it and never writes to it. From the main checkout (about 10 GB):

    git clone $ARCHIVE_URL ../millennium-dawn-archive

  The archive is read-only on GitHub, so the clone needs no updates.

FIND THE BRANCH NAME
  From the main checkout, drop the origin/ prefix from the names it lists:
    git -C ../millennium-dawn-archive branch -r

USAGE
  tools/migrate_branch.sh BRANCH           migrate, then push it yourself
  tools/migrate_branch.sh BRANCH --push    migrate, push it if the result verifies
  tools/migrate_branch.sh --help           show this help

SETTINGS
  Put these in front of the command, as in: MAP=path tools/migrate_branch.sh BRANCH

  ARCHIVE=path   Use another archive clone.
  MAP=path       The commit-map file that git filter-repo wrote during the cut.
                 Needed when a commit on the old main has no unique match,
                 which covers most branches forked before 2026.
  SKIP_FETCH=1   Do not fetch origin/main first. This works offline.

WHAT HAPPENS
  Always
    The result is compared with the archive branch before anything is created.
    The checkout stays where it is. A failed run creates no branch and pushes
    nothing. A successful run creates the local branch and leaves it there.

  Something does not match
    The run stops. Nothing is created or pushed, and the error prints where
    the two exports are so they can be compared.

  Ambiguous or missing parent
    The run stops and names the commit from the old main. Pass MAP to map a
    branch that forked before 2026. A parent whose files the cut changed is
    refused, because replaying the branch would restore removed files.

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
describe_old() {
  git -C "$ARCHIVE" log -1 --format='%h %cs %s' "$1"
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
if git show-ref --verify --quiet "refs/heads/$branch"; then
  die "local branch $branch already exists. If it is a failed attempt with nothing you need, delete it with git branch -D $branch and run this again."
fi
if [ -z "$ARCHIVE" ]; then
  common=$(git rev-parse --path-format=absolute --git-common-dir)
  ARCHIVE=$(dirname "$(dirname "$common")")/millennium-dawn-archive
fi
echo "archive: $ARCHIVE"
[ -d "$ARCHIVE" ] || die "no archive clone at $ARCHIVE. Make one with: git clone $ARCHIVE_URL '$ARCHIVE'"
[ -n "${SKIP_FETCH:-}" ] || git fetch -q origin main
assert_new_history "this clone is on the old history. Make a new clone of Millennium-Dawn and run this there." HEAD origin/main --branches --tags --remotes

old_main=$(git -C "$ARCHIVE" rev-parse --verify -q refs/remotes/origin/main) ||
  die "no origin/main in $ARCHIVE. It must be a full clone of $ARCHIVE_URL"
tip=$(git -C "$ARCHIVE" rev-parse --verify -q "refs/remotes/origin/$branch") ||
  die "no origin/$branch in $ARCHIVE. List the branches with: git -C '$ARCHIVE' branch -r"
[ "$tip" != "$old_main" ] || die "$branch has no commits of its own"

work=$(git rev-parse --path-format=absolute --git-path migrate)
mkdir -p "$work"
echo "branch forked from main at: $(describe_old "$(git -C "$ARCHIVE" merge-base "$tip" "$old_main")")"
echo "commits and merges to replay: $(git -C "$ARCHIVE" rev-list --count "$tip" --not "$old_main")"

# Mark the old main parents and their new main equivalents with the same numbers,
# so fast-export emits only this branch and fast-import attaches it to the new main.
git log origin/main --format='%T%x09%at%x09%s%x09%H' >"$work/main.tsv"
boundary=()
while IFS= read -r line; do
  boundary+=("$line")
done < <(git -C "$ARCHIVE" rev-list --boundary "$tip" --not "$old_main" | sed -n 's/^-//p')
[ ${#boundary[@]} -gt 0 ] || die "cannot find the commits on the old main that $branch builds on"
: >"$work/old.marks"
: >"$work/new.marks"
n=0
for old in "${boundary[@]}"; do
  n=$((n + 1))
  triple=$(git -C "$ARCHIVE" log -1 --format='%T%x09%at%x09%s' "$old")
  if [ -n "$MAP" ]; then
    new=$(awk -v m="$old" '$1 == m {print $2; exit}' "$MAP")
    [ -n "$new" ] || die "no line for $(describe_old "$old") in $MAP"
    git rev-parse --verify -q "$new^{commit}" >/dev/null ||
      die "$MAP maps $(describe_old "$old") to $new, which is not in this clone"
  else
    found=()
    while IFS= read -r line; do
      found+=("$line")
    done < <(awk -F'\t' -v t="$triple" 'index($0, t "\t") == 1 {print $4}' "$work/main.tsv")
    if [ ${#found[@]} -eq 0 ]; then
      die "no commit on the new main matches $(describe_old "$old"). If the branch forked before 2026, run again with MAP=/path/to/commit-map (see --help)."
    fi
    if [ ${#found[@]} -gt 1 ]; then
      die "$(describe_old "$old") matches ${#found[@]} commits on the new main. Run again with MAP=/path/to/commit-map (see --help)."
    fi
    new=${found[0]}
  fi
  git merge-base --is-ancestor "$new" origin/main || die "$new is not on the new main"
  if [ "$(git -C "$ARCHIVE" rev-parse "$old^{tree}")" != "$(git rev-parse "$new^{tree}")" ]; then
    die "the cut changed the files at $(describe_old "$old"). Replaying $branch would restore removed files, so it needs a hand migration."
  fi
  echo ":$n $old" >>"$work/old.marks"
  echo ":$n $new" >>"$work/new.marks"
done

staging=refs/migrate/result
cleanup() { git update-ref -d "$staging" 2>/dev/null || true; }
trap cleanup EXIT
git -C "$ARCHIVE" fast-export --use-done-feature --reencode=no \
  --import-marks="$work/old.marks" \
  "--refspec=refs/remotes/origin/$branch:$staging" \
  "refs/remotes/origin/$branch" --not refs/remotes/origin/main |
  git fast-import --done --quiet --import-marks="$work/new.marks" ||
  die "the replay failed. Nothing was created or pushed."
git rev-parse --verify -q "$staging^{commit}" >/dev/null ||
  die "the replay produced no commits. Nothing was created or pushed."

git -C "$ARCHIVE" fast-export --no-data --use-done-feature --reencode=no \
  --import-marks="$work/old.marks" \
  "--refspec=refs/remotes/origin/$branch:refs/heads/$branch" \
  "refs/remotes/origin/$branch" --not refs/remotes/origin/main >"$work/archive.export"
git fast-export --no-data --use-done-feature --reencode=no \
  --import-marks="$work/new.marks" \
  "--refspec=$staging:refs/heads/$branch" \
  "$staging" --not origin/main >"$work/replay.export"
if ! cmp -s "$work/archive.export" "$work/replay.export"; then
  die "the replay does not match the archive branch. Nothing was created or pushed. Compare the two exports in $work"
fi
assert_new_history "the replay still contains the old history. Do not push." "$staging"
# The replay's parents on the new main must be exactly the commits MAP or the match chose.
landed=()
while IFS= read -r line; do
  landed+=("$line")
done < <(git rev-list --boundary "$staging" --not origin/main | sed -n 's/^-//p' | sort)
[ ${#landed[@]} -gt 0 ] ||
  die "the replay is not attached to a commit on the new main. Nothing was created or pushed."
expected=()
while IFS= read -r line; do
  expected+=("$line")
done < <(sed -n 's/^:[0-9]* //p' "$work/new.marks" | sort)
[ "${landed[*]}" = "${expected[*]}" ] ||
  die "the replay is not attached to the expected commits on the new main. Nothing was created or pushed."

git branch "$branch" "$staging"
echo "ok: $branch is on the new history and matches the archive branch"
if [ "$push" = "--push" ]; then
  git push -u origin "$branch" || die "push failed. The local branch $branch is ready. If origin rejected it, see --help before retrying."
else
  echo "Not pushed. Your checkout is unchanged. To work on it: git switch $branch"
fi
