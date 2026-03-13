# Phase 4 — Review & Fix Loop

*Goal: catch and fix issues before merge. Max 3 iterations.*

---

## Overview

```
SUGGESTIONS = []
iteration = 1
while iteration <= 3:
    findings = review(PR)
    critical, important, suggestions = classify(findings)
    SUGGESTIONS.extend(suggestions)
    if no critical and no important:
        break
    fix(critical + important)
    verify_and_commit()
    iteration += 1
# Pass full SUGGESTIONS list to the final report
```

After the loop, proceed to merge (Phase 4.5 in the orchestrator).

---

## 4.1 — Review

### Preferred: External Review Tool

If an external review tool or skill is available (e.g. `pr-review-toolkit:review-pr`), use it against the PR number. Its output should already include severity classifications.

### Fallback: Structured Self-Review

If no review tool is available, you must self-review. This is inherently limited — you wrote the code, so your instinct is to think it's correct. To compensate, work through the rubric below methodically. For each category, **state what you inspected and what you found.** A review that just says "looks good" is worthless.

Read `references/review-rubric.md` for the full checklist.

### Classify Findings

Every finding gets one severity:

| Severity | Meaning | Action |
|---|---|---|
| **critical** | Broken functionality, security vulnerability, data loss risk | Must fix |
| **important** | Convention violation, performance concern, accessibility gap, missing test | Should fix |
| **suggestion** | Style preference, minor improvement, "nice to have" | Do NOT fix — append to `SUGGESTIONS` for the final report |

---

## 4.2 — Exit Check

- No critical AND no important findings → **exit loop**, proceed to merge.
- `iteration > 3` → **exit loop**, report remaining issues in the final report.

---

## 4.3 — Fix

### Domain Scoping

Group findings by domain so that no two fix efforts touch the same file.

**If the project context file defines a Review Domains table**, use it. Each domain lists allowed and forbidden file paths.

**If no domain table is defined**, infer domains from the project's directory structure. A reasonable default: one domain per top-level source subdirectory. For example, in a project with `src/components/`, `src/lib/`, `src/pages/`, and `tests/` you'd get four domains.

**The key rule:** each file belongs to exactly one domain. If a finding spans two domains (e.g. a component change requires a matching test change), assign it to the domain that owns the primary file.

### Execution

**With subagents (Claude Code):** Spawn one fix agent per non-empty domain, in parallel. Each agent receives only its scoped findings and its allowed file list.

Fix agent prompt:

```
You are a fix agent working in $WORKTREE. Use absolute paths for all file operations.

Fix these issues:
1. [file:line] <description>
2. [file:line] <description>
...

Allowed files: <list of paths/globs for this domain>
Forbidden: everything else — do NOT touch files outside your scope.

Rules:
- Fix only the listed issues. No drive-by refactors.
- If a fix requires changing a file outside your scope, describe the needed
  change in a comment and leave it for the orchestrator.
- Do NOT commit. The orchestrator commits after all agents finish.
- Do NOT run the build. The orchestrator verifies after all agents finish.
```

**Without subagents:** Fix domains sequentially. Complete all fixes in one domain before starting the next. Same rules apply — only fix listed issues, no drive-by refactors.

---

## 4.4 — Verify & Commit

After all fixes are applied:

```bash
bash "$SKILL_DIR/scripts/verify.sh" "$WORKTREE" 0 "$BUILD_CMD" "$TEST_CMD" "$LINT_CMD"
```

If verification fails, fix the regression (cap: 3 attempts for this sub-step). Then:

```bash
cd "$WORKTREE" && git add -A && git commit -m "fix: address review findings (iteration $iteration)"
cd "$WORKTREE" && git push
```

Increment `iteration`, return to 4.1.
