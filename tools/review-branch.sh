#!/usr/bin/env bash
# review-branch.sh — Show a summary of all changes on the current branch vs main

set -euo pipefail

MAIN_BRANCH="${1:-main}"
CURRENT=$(git branch --show-current)

echo "========================================"
echo "Branch:  $CURRENT"
echo "Base:    $MAIN_BRANCH"
echo "========================================"
echo ""

echo "--- Commits ---"
git log "$MAIN_BRANCH..HEAD" --oneline
echo ""

echo "--- Changed files ---"
git diff "$MAIN_BRANCH...HEAD" --stat
echo ""

echo "--- Changes by directory ---"
git diff "$MAIN_BRANCH...HEAD" --name-only \
  | sed 's|/[^/]*$||' \
  | sort | uniq -c | sort -rn \
  | awk '{printf "  %3d  %s\n", $1, $2}'
echo ""

echo "--- Full diff ---"
git diff "$MAIN_BRANCH...HEAD"
