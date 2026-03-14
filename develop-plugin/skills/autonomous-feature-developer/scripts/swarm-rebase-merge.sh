#!/usr/bin/env bash
# swarm-rebase-merge.sh — Rebase a feature branch onto the updated base branch
# and merge its PR. Used by the /swarm sequential merge queue.
#
# Usage:
#   bash swarm-rebase-merge.sh <worktree> <branch> <base-branch> \
#     <pr-number> <pr-cli> <merge-strategy> <repo-root>
#
# Arguments:
#   worktree        — absolute path to the feature's worktree
#   branch          — feature branch name (e.g. feature/auth)
#   base-branch     — branch to rebase onto (e.g. main)
#   pr-number       — PR/MR number to merge after successful rebase
#   pr-cli          — "gh" or "glab"
#   merge-strategy  — "--squash", "--rebase", or "--merge"
#   repo-root       — absolute path to the main repository
#
# Exit codes:
#   0  — rebased and merged successfully
#   1  — rebase conflict (caller must resolve or mark as failed)
#   2  — merge CLI failure (network, auth, permissions, etc.)
#   3  — push rejected (force-with-lease race condition — retry once)
#
# IMPORTANT: This script uses git push --force-with-lease. The default
# permissions deny list includes "Bash(git push --force*)". You must either:
# (A) Add "Bash(git push --force-with-lease*)" to permissions.allow in
#     .claude/settings.local.json (allow overrides deny for same pattern), or
# (B) Replace the push step with: git push origin --delete "$BRANCH" && git push origin "$BRANCH"
# Document your chosen approach here before shipping.

set -uo pipefail

WORKTREE="${1:?Usage: swarm-rebase-merge.sh <worktree> <branch> <base-branch> <pr-number> <pr-cli> <merge-strategy> <repo-root>}"
BRANCH="${2:?}"
BASE_BRANCH="${3:?}"
PR_NUMBER="${4:?}"
PR_CLI="${5:?}"
MERGE_STRATEGY="${6:---squash}"
REPO_ROOT="${7:?}"

# Fetch latest state of the base branch
git -C "$REPO_ROOT" fetch origin "$BASE_BRANCH"

# Perform rebase in the feature worktree
cd "$WORKTREE"
if ! git rebase "origin/${BASE_BRANCH}"; then
  echo "REBASE_CONFLICT: ${BRANCH}" >&2
  echo "CONFLICT_FILES:"
  git diff --name-only --diff-filter=U
  git rebase --abort
  exit 1
fi

# Push the rebased branch
if ! git push --force-with-lease origin "$BRANCH"; then
  echo "PUSH_REJECTED: ${BRANCH}" >&2
  exit 3
fi

# Merge the PR/MR
case "$PR_CLI" in
  gh)
    if gh pr merge "$PR_NUMBER" "$MERGE_STRATEGY" --delete-branch 2>&1; then
      echo "MERGED: PR #${PR_NUMBER}"
      exit 0
    else
      echo "MERGE_FAILED: PR #${PR_NUMBER}" >&2
      exit 2
    fi
    ;;
  glab)
    GLAB_FLAGS="--remove-source-branch"
    case "$MERGE_STRATEGY" in
      --squash) GLAB_FLAGS="$GLAB_FLAGS --squash" ;;
      --rebase) GLAB_FLAGS="$GLAB_FLAGS --rebase" ;;
      # --merge is glab default, no flag needed
    esac
    # shellcheck disable=SC2086  # GLAB_FLAGS is intentionally word-split
    if glab mr merge "$PR_NUMBER" $GLAB_FLAGS 2>&1; then
      echo "MERGED: MR !${PR_NUMBER}"
      exit 0
    else
      echo "MERGE_FAILED: MR !${PR_NUMBER}" >&2
      exit 2
    fi
    ;;
  *)
    echo "ERROR: unsupported PR CLI '${PR_CLI}'. Use 'gh' or 'glab'." >&2
    exit 2
    ;;
esac
