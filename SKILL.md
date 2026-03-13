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
cp <skill-dir>/assets/project-context.template.md docs/project-context.md
```

Then fill it in. The skill won't proceed without one.

---

## Pipeline Overview

| Phase | What happens | Reads |
|---|---|---|
| **0 — Setup** | Create worktree + branch | Context file |
| **1 — Architecture** | Explore codebase, write plan | `references/phase-1-architecture.md` |
| **2 — Implementation** | Code the plan, verify build/tests | `references/phase-2-implementation.md` |
| **3 — Pull Request** | Push, open PR | `references/phase-3-pull-request.md` |
| **4 — Review & Fix** | Review → fix → verify loop (max 3) | `references/phase-4-review-fix.md`, `references/review-rubric.md` |
| **4.5 — Merge** | Squash/rebase/merge the PR | *(inline below)* |
| **5 — Cleanup** | Remove worktree | *(inline below)* |

Read each reference file **at the start of that phase**, not all upfront.

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

The path to the context file itself is `$CONTEXT_FILE`, captured from `setup.sh` output. To use a non-default location, pass it as the second argument to `setup.sh` (see Phase 0).

These variables are passed to scripts as arguments or environment variables.

---

## Phase 0 — Setup

First, set `SKILL_DIR` to the absolute path of the directory containing this `SKILL.md` file.

Run the setup script with the feature request as the argument. An alternate context file path may be passed as a second argument — omit it to use the default (`docs/project-context.md`):

```bash
bash "$SKILL_DIR/scripts/setup.sh" "<feature request text>" [optional-context-file-path]
```

The script outputs six values. Capture them all for subsequent phases:

```
SLUG=...
BRANCH=...
WORKTREE=...
PLAN_FILE=...
SKILL_DIR=...       # confirms resolved skill directory
CONTEXT_FILE=...    # path to the project context file
```

Then read `$CONTEXT_FILE`.

## Phase 1 — Architecture

Read `references/phase-1-architecture.md` and follow its instructions. Produces a plan file at `$WORKTREE/$PLAN_FILE`. No source code changes.

## Phase 2 — Implementation

Read `references/phase-2-implementation.md` and follow its instructions. Uses `scripts/verify.sh` for build/test/lint with retry caps.

## Phase 3 — Pull Request

Read `references/phase-3-pull-request.md` and follow its instructions. Uses `scripts/create-pr.sh` for multi-platform PR creation. Capture `PR_NUMBER` and `PR_URL`.

## Phase 4 — Review & Fix Loop

Read `references/phase-4-review-fix.md` and follow its instructions. Loops up to 3 iterations. Uses `scripts/verify.sh` after each fix round.

## Phase 4.5 — Merge

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
bash "$SKILL_DIR/scripts/merge-cleanup.sh" merge "$PR_NUMBER" "$PR_CLI" "$MERGE_STRATEGY"
```

- Exit code 0 → `merged = yes`
- Non-zero → report the error from stderr, `merged = no`

## Phase 5 — Cleanup

```bash
bash "$SKILL_DIR/scripts/merge-cleanup.sh" cleanup "$WORKTREE"
```

Always runs, regardless of merge outcome.

---

## Aborting & Recovery

If the pipeline is interrupted at any phase, run cleanup manually to remove the worktree:

```bash
bash "$SKILL_DIR/scripts/merge-cleanup.sh" cleanup "$WORKTREE"
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
