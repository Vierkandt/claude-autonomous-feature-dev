# Agent Bug Report Protocol

When an auto-dev agent encounters an error it cannot recover from, it writes a structured bug report before writing the done marker. This provides debugging context for the orchestrator, dashboard, and human operators.

## File location

`docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-bug-report.md`

For standalone `/auto-dev` (no swarm): `.worktrees/<slug>/bug-report.md` in the worktree.

## Format

The bug report is markdown for human readability:

```markdown
# Bug Report — <workbranch name>

**Date:** <ISO 8601 timestamp>
**Phase:** <phase number and name where the error occurred>
**Workbranch:** <slug>
**Branch:** <git branch name>
**Worktree:** <absolute path>

## What was being attempted

<1-2 sentences: what the agent was trying to do when it failed>

## Error

```
<the actual error output — last 50 lines of build/test/lint output,
or the exception message, or the git error>
```

## Relevant files

<list of files the agent was working on when the error occurred>
- `path/to/file.ts` — <what was being done to this file>

## Root cause analysis

<agent's best assessment of why the error occurred>
- Is this a code bug, a configuration issue, a missing dependency, or a contract conflict?
- If the agent tried multiple fix attempts, summarize what was tried

## Suggested fix

<what the agent thinks would fix the issue, if it has an idea>

## Context

- Sub-feature being implemented: <name and index>
- Build command: <the command that was run>
- Build status at time of failure: <passing/failing>
- Review iteration: <N, if in Phase 4>
- Contract deviations noticed: <any>
- Files created this session: <list>
- Files modified this session: <list>
- Commits made: <count>
```

## When to write

Write a bug report when:
- Build fails after exhausting all retry attempts (Phase 2)
- Test fails after exhausting all retry attempts (Phase 2)
- Lint fails after exhausting all retry attempts (Phase 2)
- Phase 1 sync timeout occurs
- wait_for dependency fails
- PR creation fails (Phase 3)
- Review loop exhausted without resolving critical issues (Phase 4)
- Any unexpected error that terminates the agent

Do NOT write a bug report for:
- Intermediate failures that are retried and succeed
- Normal completion (even with suggestions remaining)

## Rules

- Write the bug report BEFORE writing the done marker (Phase 5.5)
- Bug report writes are fire-and-forget — failure to write must never block the pipeline
- Include actual error output, not just "build failed" — the raw output is the most valuable part
- Limit error output to the last 50 lines to avoid massive files
- The root cause analysis should be the agent's honest assessment, not a guess that sounds confident
