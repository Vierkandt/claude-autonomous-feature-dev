#!/usr/bin/env bash
# merge-cleanup.sh — Merge a PR/MR or remove a worktree.
#
# Usage:
#   bash merge-cleanup.sh merge  <pr-number> <pr-cli> <merge-strategy>
#   bash merge-cleanup.sh cleanup <worktree-path>
#
# Subcommands:
#   merge   — Merge the PR/MR using the given strategy. Exit 0 on success, 1 on failure.
#   cleanup — Force-remove the worktree. Always attempted, errors are non-fatal.

set -uo pipefail

ACTION="${1:?Usage: merge-cleanup.sh <merge|cleanup> ...}"
shift

case "$ACTION" in
  merge)
    PR_NUMBER="${1:?merge requires: <pr-number> <pr-cli> <merge-strategy>}"
    PR_CLI="${2:?}"
    MERGE_STRATEGY="${3:---squash}"

    case "$PR_CLI" in
      gh)
        if gh pr merge "$PR_NUMBER" "$MERGE_STRATEGY" --delete-branch 2>&1; then
          echo "MERGED: PR #${PR_NUMBER}"
          exit 0
        else
          echo "MERGE_FAILED: PR #${PR_NUMBER}" >&2
          exit 1
        fi
        ;;
      glab)
        # Map strategy flags for glab
        GLAB_FLAGS="--remove-source-branch"
        case "$MERGE_STRATEGY" in
          --squash) GLAB_FLAGS="$GLAB_FLAGS --squash" ;;
          --rebase) GLAB_FLAGS="$GLAB_FLAGS --rebase" ;;
          # --merge is glab's default
        esac
        if glab mr merge "$PR_NUMBER" $GLAB_FLAGS 2>&1; then  # GLAB_FLAGS is intentionally unquoted (multiple flags)
          echo "MERGED: MR !${PR_NUMBER}"
          exit 0
        else
          echo "MERGE_FAILED: MR !${PR_NUMBER}" >&2
          exit 1
        fi
        ;;
      *)
        echo "ERROR: unsupported PR CLI '${PR_CLI}'." >&2
        exit 1
        ;;
    esac
    ;;

  cleanup)
    WORKTREE="${1:?cleanup requires: <worktree-path>}"
    echo "Removing worktree: ${WORKTREE}"
    git worktree remove "$WORKTREE" --force 2>&1 || echo "WARN: worktree removal failed (may already be gone)"
    exit 0
    ;;

  *)
    echo "ERROR: unknown action '${ACTION}'. Use 'merge' or 'cleanup'." >&2
    exit 1
    ;;
esac
