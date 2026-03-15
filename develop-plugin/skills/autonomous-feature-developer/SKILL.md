---
name: autonomous-feature-developer
description: Use when the user wants to autonomously build a feature end-to-end with zero interaction. Handles architecture, implementation, PR creation, review, and automated fix cycles. Trigger on phrases like "build this feature", "implement this end-to-end", "autonomous feature", "auto-develop", or when someone describes a feature and asks for it to be fully built, reviewed, and merged without hand-holding. Also use when someone says "ship this" or "just make it happen".
---

# Autonomous Feature Developer

Builds a feature from request to merged PR in a single run.

## Requirements

- **Git** with worktree support
- **Git hosting CLI** — `gh` (GitHub) or `glab` (GitLab)
- **Claude Code** or equivalent agent environment with filesystem + shell access
- *(Strongly recommended)* An external **code review tool/skill**

## Quick Start

If the project doesn't have a context file yet, copy the template to get started:

```bash
cp "${CLAUDE_SKILL_DIR}/assets/project-context.template.md" docs/project-context.md
```

Then fill it in. The skill won't proceed without one.

---

## Pipeline Overview

| Phase | What happens | Reads |
|---|---|---|
| **0 — Setup** | Create worktree + branch | Context file |
| **1 — Architecture** | Explore codebase, write plan | `references/phase-1-architecture.md`, `docs/project-contract.md` (if exists), `docs/wave-learnings.md` (if exists, wave 2+) |
| **2 — Implementation** | Code the plan, verify build/tests | `references/phase-2-implementation.md` |
| **3 — Pull Request** | Push, open PR | `references/phase-3-pull-request.md` |
| **4 — Review & Fix** | Review → fix → verify loop (max 3) | `references/phase-4-review-fix.md`, `references/review-rubric.md` |
| **4.5 — Merge** | Squash/rebase/merge the PR | *(inline below)* |
| **5 — Cleanup** | Remove worktree | *(inline below)* |

Read each reference file **at the start of that phase**, not all upfront. Reference file paths are relative to `${CLAUDE_SKILL_DIR}`.

---

## Context File

Read `docs/project-context.md` (or user-specified path) before anything else. Extract these variables — use the defaults shown if the context file omits them:

| Variable | Context file location | Default |
|---|---|---|
| `BASE_BRANCH` | Git / PR Conventions → base branch | `main` |
| `BUILD_CMD` | Build & Run → build | `npm run build` |
| `TEST_CMD` | Build & Run → test | *(empty — skip)* |
| `LINT_CMD` | Build & Run → lint | *(empty — skip)* |
| `MERGE_STRATEGY` | Git / PR Conventions → merge strategy | `--squash` |
| `PR_CLI` | Git / PR Conventions → hosting CLI | `gh` |
| `CONTRACT_FILE` | Derived: `docs/project-contract.md` at `$REPO_ROOT` | `docs/project-contract.md` |
| `LEARNINGS_FILE` | Derived: `docs/wave-learnings.md` at `$REPO_ROOT` | `docs/wave-learnings.md` |

The path to the context file itself is `$CONTEXT_FILE`, captured from `setup.sh` output. To use a non-default location, pass it as the second argument to `setup.sh` (see Phase 0).

These variables are passed to scripts as arguments or environment variables.

These files may not exist for standalone `/auto-dev` invocations. The skill checks for their existence before reading them — missing files are skipped silently.

---

## Swarm Context

When invoked via `/swarm`, additional variables are passed:

| Variable | Meaning |
|---|---|
| `WORKBRANCH_FILE` | Path to the workbranch file for this feature |
| `WORKBRANCH_SLUG` | Slug of this workbranch (filename without .md) |
| `PLAN_SLUG` | Slug of the parent plan |
| `WORKBRANCH_SUBFEATURES` | Newline-separated list of sub-feature descriptions from the workbranch file |
| `PHASE1_SYNC` | `"true"` — agent must perform Phase 1 sync point protocol |

If `WORKBRANCH_FILE` is empty, this is a standalone invocation. All swarm-specific steps are no-ops.

---

## Progress Reporting (swarm invocation only)

If `WORKBRANCH_FILE` is non-empty, write a progress heartbeat after every significant event. See `${CLAUDE_SKILL_DIR}/references/progress-protocol.md` for the full protocol.

Progress file path: `docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-progress.json`

Write progress using:
```bash
cat > "docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-progress.json" << PROGRESS_EOF
{
  "workbranch": "$WORKBRANCH_SLUG",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  ... (fill in current values)
}
PROGRESS_EOF
```

If the write fails, continue — progress reporting must never block the pipeline.

## Bug Reporting

When any phase encounters an unrecoverable error, write a bug report before the done marker. See `${CLAUDE_SKILL_DIR}/references/bug-report-protocol.md` for the full protocol.

**Swarm invocations:** Write to `docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-bug-report.md`
**Standalone invocations:** Write to the worktree root as `bug-report.md`

The bug report must include the actual error output (last 50 lines), what was being attempted, which files were involved, and the agent's honest root cause analysis. Write this BEFORE the done marker (Phase 5.5).

If the bug report write fails, continue — it must never block the pipeline.

---

## Worktree Rules

You are running inside an isolated worktree managed by the swarm system. These rules are mandatory:

- **Do NOT** run `git worktree add` — you are already in a worktree
- **Do NOT** create directories named `.worktrees/` or `worktrees/`
- **Do NOT** write to or create `.claude/settings.local.json` — this overrides permissions for all agents
- **Do NOT** create nested worktrees (worktree inside a worktree)
- If `.git` is a file (not a directory), you are in a worktree — work from your current directory
- All your work happens in the current working directory. Do not attempt to `cd` to the project root or another worktree.

If you detect that you are about to write `.claude/settings.local.json`, STOP. This file controls permissions for the entire session and must not be modified by feature agents.

---

## Phase 0 — Setup

Run the setup script with the feature request as the argument. An alternate context file path may be passed as a second argument — omit it to use the default (`docs/project-context.md`):

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh" "<feature request text>" [optional-context-file-path]
```

The script outputs five values. Capture them all for subsequent phases:

```
SLUG=...
BRANCH=...
WORKTREE=...
PLAN_FILE=...
CONTEXT_FILE=...    # path to the project context file
```

Then read `$CONTEXT_FILE`.

## Phase 1 — Architecture

Read `${CLAUDE_SKILL_DIR}/references/phase-1-architecture.md` and follow its instructions. Produces a plan file at `$PLAN_FILE`. No source code changes.

## Phase 2 — Implementation

Read `${CLAUDE_SKILL_DIR}/references/phase-2-implementation.md` and follow its instructions. Uses `scripts/verify.sh` for build/test/lint with retry caps.

## Phase 3 — Pull Request

Read `${CLAUDE_SKILL_DIR}/references/phase-3-pull-request.md` and follow its instructions. Uses `scripts/create-pr.sh` for multi-platform PR creation. Capture `PR_NUMBER` and `PR_URL`.

## Phase 4 — Review & Fix Loop

Read `${CLAUDE_SKILL_DIR}/references/phase-4-review-fix.md` and follow its instructions. Loops up to 3 iterations. Uses `scripts/verify.sh` after each fix round.

## Phase 4.5 — Merge

**Swarm invocation only:** If `WORKBRANCH_FILE` is non-empty, skip Phase 4.5 entirely.
The /swarm command manages all merging via the sequential merge queue. Proceed directly
to Phase 5.5 (Write done marker), then Phase 5 (Cleanup).

Before merging, delete the plan file so it does not appear in the squash commit:

```bash
rm -f "$PLAN_FILE"
rmdir "$WORKTREE/docs/plans" "$WORKTREE/docs" 2>/dev/null || true
git -C "$WORKTREE" add -u
git -C "$WORKTREE" commit -m "chore: remove implementation plan"
git -C "$WORKTREE" push
```

Then merge:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/merge-cleanup.sh" merge "$PR_NUMBER" "$PR_CLI" "$MERGE_STRATEGY"
```

- Exit code 0 → `merged = yes`
- Non-zero → report the error from stderr, `merged = no`

## Phase 5 — Cleanup

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/merge-cleanup.sh" cleanup "$WORKTREE"
```

Always runs, regardless of merge outcome.

---

## Phase 5.5 — Write done marker (swarm invocation only)

If `WORKBRANCH_FILE` is empty, skip this phase.

Write the done marker before performing Phase 5 cleanup. Path:

```
docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-done.json
```

On success (review loop completed, PR open and ready to merge):

```json
{
  "workbranch": "<WORKBRANCH_SLUG>",
  "status": "merged",
  "pr_url": "<PR_URL>",
  "pr_number": "<PR_NUMBER>",
  "merged": false,
  "branch": "<BRANCH>",
  "worktree": "<WORKTREE>",
  "review_iterations": <N>,
  "contract_deviations": ["<deviation description if any, or empty array>"]
}
```

Note: `"merged": false` because `/swarm` handles merging. Status `"merged"` here means "ready to merge — PR is open, review loop complete."

On failure (any phase failed to complete):

If the status is "failed", write the bug report first (see Bug Reporting section above), then write the done marker.

```json
{
  "workbranch": "<WORKBRANCH_SLUG>",
  "status": "failed",
  "pr_url": "<PR_URL or empty string>",
  "pr_number": "<PR_NUMBER or empty string>",
  "merged": false,
  "branch": "<BRANCH>",
  "worktree": "<WORKTREE>",
  "review_iterations": <N>,
  "contract_deviations": [],
  "error": "<one to two sentence summary of what failed and why>",
  "bug_report": "docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-bug-report.md"
}
```

Write the done marker even if Phase 5 cleanup subsequently fails.

---

## Aborting & Recovery

If the pipeline is interrupted at any phase, run cleanup manually to remove the worktree:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/merge-cleanup.sh" cleanup "$WORKTREE"
```

To list all active worktrees:

```bash
git worktree list
```

If `$WORKTREE` was never captured, re-run Phase 0 with the same feature request — `setup.sh` detects the existing worktree and branch and reuses them without creating duplicates.

---

## Done

Report:

| Field | Value |
|---|---|
| **PR URL** | `$PR_URL` |
| **Summary** | one-line description of what was built |
| **Review iterations** | count completed |
| **Remaining suggestions** | informational findings not acted on |
| **Remaining issues** | unresolved critical/important (if hit max iterations) |
| **Build / test failures** | any that couldn't be resolved |
| **Merged** | yes / no (with reason if no) |
| **Status** | clean / issues remain |
