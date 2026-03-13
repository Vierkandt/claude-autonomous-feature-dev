#!/usr/bin/env bash
# setup.sh — Derive slug from feature request, create worktree + branch.
# Usage: bash setup.sh "<feature request text>"
# Output: prints SLUG, BRANCH, WORKTREE, PLAN_FILE to stdout (one per line, KEY=VALUE)

set -euo pipefail

FEATURE_REQUEST="${1:?Usage: setup.sh \"<feature request text>\"}"

# Derive slug: lowercase, non-alphanum → hyphens, collapse, strip, truncate
SLUG=$(echo "$FEATURE_REQUEST" \
  | tr '[:upper:]' '[:lower:]' \
  | sed 's/[^a-z0-9]/-/g' \
  | sed 's/-\+/-/g' \
  | sed 's/^-//;s/-$//' \
  | cut -c1-50)

BRANCH="feature/${SLUG}"
WORKTREE=".worktrees/${SLUG}"
PLAN_FILE="docs/plans/${SLUG}-plan.md"

# Find repo root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Create worktree + branch
git -C "$REPO_ROOT" worktree add "${REPO_ROOT}/${WORKTREE}" -b "$BRANCH"
mkdir -p "${REPO_ROOT}/${WORKTREE}/docs/plans"

# Output variables for the orchestrator to capture
echo "SLUG=${SLUG}"
echo "BRANCH=${BRANCH}"
echo "WORKTREE=${REPO_ROOT}/${WORKTREE}"
echo "PLAN_FILE=${PLAN_FILE}"
