# Agent Progress Protocol

When `WORKBRANCH_FILE` is non-empty (swarm invocation), the agent writes a progress heartbeat file after every significant event. This file is read by the swarm dashboard for live status updates.

## File location

`docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-progress.json`

## Format

```json
{
  "workbranch": "<WORKBRANCH_SLUG>",
  "timestamp": "<ISO 8601>",
  "phase": <0-5>,
  "phase_name": "<Setup|Architecture|Implementation|Pull Request|Review & Fix|Cleanup>",
  "sub_feature_index": <current, 0-based>,
  "sub_feature_total": <total>,
  "sub_feature_name": "<name of current sub-feature>",
  "current_action": "<human-readable description of what's happening right now>",
  "files_created": ["<path>", ...],
  "files_modified": ["<path>", ...],
  "build_status": "<passing|failing|not_run>",
  "test_status": "<passing|failing|not_run|skipped>",
  "commits": <number>,
  "errors": ["<error message if any>"]
}
```

## When to write

| Event | phase | current_action |
|---|---|---|
| Phase 0 starts | 0 | "Creating worktree and branch" |
| Phase 0 complete | 0 | "Worktree created" |
| Phase 1 starts | 1 | "Reading project contract and exploring codebase" |
| Phase 1 plan committed | 1 | "Architecture plan committed" |
| Phase 1 sync waiting | 1 | "Waiting for Phase 1 sync resolution" |
| Phase 1 sync resolved | 1 | "Phase 1 sync complete, proceeding to implementation" |
| Phase 2 starts | 2 | "Implementing: <first sub-feature name>" |
| Each sub-feature committed | 2 | "Implementing: <next sub-feature name>" (increment sub_feature_index, update files_created/modified, commits) |
| Build passes | 2 | (update build_status to "passing") |
| Build fails | 2 | (update build_status to "failing", add to errors) |
| Phase 3 PR created | 3 | "PR #N opened" |
| Phase 4 review starts | 4 | "Review iteration N" |
| Phase 4 fixes applied | 4 | "Applied N fixes, verifying" |
| Phase 5.5 done marker | 5 | "Complete" |

## Rules

- Progress writes are fire-and-forget. Failure to write must NEVER block the pipeline.
- Always overwrite the file (not append). The dashboard reads the latest state.
- Write after the event completes, not before.
