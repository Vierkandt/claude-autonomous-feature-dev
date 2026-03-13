#!/usr/bin/env bash
# create-pr.sh — Push branch and create a pull/merge request.
# Usage: bash create-pr.sh <worktree> <base-branch> <head-branch> <pr-cli> <title> <body-file>
#
# Arguments:
#   worktree     — absolute path to worktree
#   base-branch  — target branch (e.g. main)
#   head-branch  — source branch (e.g. feature/add-dark-mode)
#   pr-cli       — "gh" or "glab"
#   title        — PR/MR title string
#   body-file    — path to a file containing the PR body (markdown)
#
# Output: prints PR_URL=... and PR_NUMBER=... to stdout.

set -euo pipefail

WORKTREE="${1:?Usage: create-pr.sh <worktree> <base-branch> <head-branch> <pr-cli> <title> <body-file>}"
BASE_BRANCH="${2:?}"
HEAD_BRANCH="${3:?}"
PR_CLI="${4:?}"
TITLE="${5:?}"
BODY_FILE="${6:?}"

cd "$WORKTREE"

# Push
git push -u origin "$HEAD_BRANCH"

# Create PR/MR
case "$PR_CLI" in
  gh)
    RESULT=$(gh pr create \
      --title "$TITLE" \
      --base "$BASE_BRANCH" \
      --head "$HEAD_BRANCH" \
      --body-file "$BODY_FILE" \
      2>&1)
    # gh pr create prints the URL on success
    PR_URL=$(echo "$RESULT" | tail -1)
    PR_NUMBER=$(gh pr view "$HEAD_BRANCH" --json number --jq '.number')
    ;;
  glab)
    RESULT=$(glab mr create \
      --title "$TITLE" \
      --target-branch "$BASE_BRANCH" \
      --source-branch "$HEAD_BRANCH" \
      --description "$(cat "$BODY_FILE")" \
      --no-editor \
      2>&1)
    PR_URL=$(echo "$RESULT" | grep -oP 'https://\S+')
    PR_NUMBER=$(echo "$RESULT" | grep -oP '!\d+' | tr -d '!')
    ;;
  *)
    echo "ERROR: unsupported PR CLI '${PR_CLI}'. Use 'gh' or 'glab'." >&2
    exit 1
    ;;
esac

echo "PR_URL=${PR_URL}"
echo "PR_NUMBER=${PR_NUMBER}"
