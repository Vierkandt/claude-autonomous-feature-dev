#!/usr/bin/env bash
# verify.sh — Run build, test, and lint commands with a retry cap.
# Usage: bash verify.sh <worktree> <max-retries> <build-cmd> [test-cmd] [lint-cmd]
#
# Arguments:
#   worktree     — absolute path to the worktree
#   max-retries  — how many times to retry each failing step (0 = run once, no retries)
#   build-cmd    — required build command (e.g. "npm run build")
#   test-cmd     — optional test command (pass "" or omit to skip)
#   lint-cmd     — optional lint command (pass "" or omit to skip)
#
# Exit codes:
#   0  — all steps passed
#   1  — one or more steps failed after all retries exhausted
#   2  — a step failed but retries remain — return control to agent to fix, then re-run
#
# Output: prints PASS/FAIL per step, and the failing command + output on failure.

set -uo pipefail

WORKTREE="${1:?Usage: verify.sh <worktree> <max-retries> <build-cmd> [test-cmd] [lint-cmd]}"
MAX_RETRIES="${2:-0}"
BUILD_CMD="${3:?build-cmd is required}"
TEST_CMD="${4:-}"
LINT_CMD="${5:-}"

cd "$WORKTREE"

run_step() {
  local label="$1"
  local cmd="$2"
  local attempt=0
  local max=$((MAX_RETRIES + 1))

  if [ -z "$cmd" ]; then
    echo "SKIP: ${label} (no command configured)"
    return 0
  fi

  while [ $attempt -lt $max ]; do
    attempt=$((attempt + 1))
    echo "RUN: ${label} (attempt ${attempt}/${max})"

    local output
    if output=$(eval "$cmd" 2>&1); then
      echo "PASS: ${label}"
      return 0
    else
      echo "FAIL: ${label} (attempt ${attempt}/${max})"
      if [ $attempt -eq $max ]; then
        echo "--- ${label} output ---"
        echo "$output" | tail -40
        echo "--- end ---"
        echo "EXHAUSTED: ${label} failed after ${max} attempts"
        return 1
      fi
      # Print last 20 lines of output so the agent can diagnose and fix
      echo "--- ${label} error (attempt ${attempt}) ---"
      echo "$output" | tail -20
      echo "--- end ---"
      echo "WAITING: return control to agent for fixes before retry"
      return 2  # signal: failed but retries remain
    fi
  done
}

OVERALL=0

run_step "build" "$BUILD_CMD"
rc=$?
[ $rc -ne 0 ] && OVERALL=1
# If build hard-failed (exit 1), skip test/lint — they'll fail too
if [ $rc -eq 1 ]; then
  echo ""
  echo "RESULT: build failed after all retries. Skipping test and lint."
  exit 1
fi
# If build needs a fix-and-retry (exit 2), stop here so agent can fix
if [ $rc -eq 2 ]; then
  exit 2
fi

run_step "test" "$TEST_CMD"
rc=$?
[ $rc -ne 0 ] && OVERALL=1
[ $rc -eq 2 ] && exit 2

run_step "lint" "$LINT_CMD"
rc=$?
[ $rc -ne 0 ] && OVERALL=1
[ $rc -eq 2 ] && exit 2

echo ""
if [ $OVERALL -eq 0 ]; then
  echo "RESULT: all steps passed"
else
  echo "RESULT: one or more steps failed"
fi
exit $OVERALL
