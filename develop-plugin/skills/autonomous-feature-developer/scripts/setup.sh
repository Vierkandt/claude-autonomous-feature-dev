#!/usr/bin/env bash
# setup.sh — Derive slug from feature request, create worktree + branch.
# Usage: bash setup.sh "<feature request text>" [context-file-path]
#
# Output: prints KEY=VALUE pairs to stdout (one per line):
#   SLUG, BRANCH, WORKTREE, PLAN_FILE, CONTEXT_FILE

set -euo pipefail

FEATURE_REQUEST="${1:?Usage: setup.sh \"<feature request text>\" [context-file-path]}"
CONTEXT_FILE_ARG="${2:-}"
CONTRACT_FILE_ARG="${3:-}"

# Resolve skill directory from script location (used only for error messages)
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Derive slug: lowercase, non-alphanum → hyphens, collapse, strip, truncate
SLUG=$(echo "$FEATURE_REQUEST" \
  | tr '[:upper:]' '[:lower:]' \
  | sed 's/[^a-z0-9]/-/g' \
  | sed 's/-\+/-/g' \
  | sed 's/^-//;s/-$//' \
  | cut -c1-50)

BRANCH="feature/${SLUG}"

# Find repo root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Worktree lives outside the repo to avoid polluting IDE file watchers and build tools
WORKTREE="${TMPDIR:-/tmp}/worktrees/${SLUG}"

# Plan file lives inside the worktree so it can be committed for resilience,
# then deleted before merge so it does not appear in the final squash commit.
PLAN_FILE="${WORKTREE}/docs/plans/${SLUG}-plan.md"

# Resolve context file path (default: docs/project-context.md at repo root)
if [ -n "$CONTEXT_FILE_ARG" ]; then
  CONTEXT_FILE="$CONTEXT_FILE_ARG"
else
  CONTEXT_FILE="${REPO_ROOT}/docs/project-context.md"
fi

# Validate context file exists before doing anything irreversible
if [ ! -f "$CONTEXT_FILE" ]; then
  echo "ERROR: context file not found: ${CONTEXT_FILE}" >&2
  echo "  Copy the template: cp ${SKILL_DIR}/assets/project-context.template.md ${CONTEXT_FILE}" >&2
  echo "  Or specify an alternate path: bash setup.sh \"<feature>\" <path-to-context>" >&2
  exit 1
fi

# Validate contract file if specified (swarm context); non-fatal if not specified
if [ -n "$CONTRACT_FILE_ARG" ]; then
  if [ ! -f "$CONTRACT_FILE_ARG" ]; then
    echo "ERROR: contract file not found: ${CONTRACT_FILE_ARG}" >&2
    echo "  Run /plan or /import-plan to generate it." >&2
    exit 1
  fi
  CONTRACT_FILE="$CONTRACT_FILE_ARG"
else
  # Default location — not validated (optional for standalone auto-dev)
  CONTRACT_FILE="${REPO_ROOT}/docs/project-contract.md"
fi

# Idempotency: reuse existing worktree/branch if already created
WORKTREE_EXISTS=false
if git -C "$REPO_ROOT" worktree list --porcelain | grep -qF "worktree ${WORKTREE}"; then
  echo "# INFO: worktree already exists at ${WORKTREE} — reusing" >&2
  WORKTREE_EXISTS=true
fi

if [ "$WORKTREE_EXISTS" = false ]; then
  mkdir -p "$(dirname "$WORKTREE")"
  if git -C "$REPO_ROOT" branch --list "$BRANCH" | grep -q .; then
    echo "# INFO: branch ${BRANCH} already exists — creating worktree for existing branch" >&2
    git -C "$REPO_ROOT" worktree add "$WORKTREE" "$BRANCH"
  else
    git -C "$REPO_ROOT" worktree add "$WORKTREE" -b "$BRANCH"
  fi
fi

mkdir -p "$(dirname "$PLAN_FILE")"

# Output variables for the orchestrator to capture
echo "SLUG=${SLUG}"
echo "BRANCH=${BRANCH}"
echo "WORKTREE=${WORKTREE}"
echo "PLAN_FILE=${PLAN_FILE}"
echo "CONTEXT_FILE=${CONTEXT_FILE}"
echo "CONTRACT_FILE=${CONTRACT_FILE}"
