# Swarm Report Template

Use this template when composing the final swarm report. Substitute all angle-bracket placeholders with actual values from the swarm state.

```markdown
# Swarm Report — <Platform Name>

**Date:** <ISO 8601 timestamp>
**Plan:** <relative path to plan file>
**Contract:** docs/project-contract.md
**Learnings:** docs/wave-learnings.md
**Duration:** <wall-clock time, e.g. "2h 14m">

## Summary

| Metric | Value |
|---|---|
| Features planned | N |
| Features merged | N |
| Features failed | N |
| Features blocked | N |
| Waves executed | N |
| Contract updates | N |
| Integration PR | <URL or "none needed"> |
| Rollback tags | swarm/<slug>/pre-wave-1 through post-wave-<N> |

## Wave Execution

### Wave <N>
- **Features:** <name> (merged), <name> (merged)
- **Merge order:** <name> -> <name>
- **Phase 1 sync:** <"no ownership conflicts" or "N conflicts resolved: <description>">
- **Wave transition:** <N issues found>, <N auto-fixed>, <N warnings>, <N contract updates>, <N learnings>
- **Halt check:** <"N% blocked -> continue" or "N% blocked -> HALT">

## Features

### <Feature Name>
- **Status:** merged | failed | blocked
- **Wave:** N
- **Sub-features:** N completed / N planned
- **PR:** <URL>
- **Branch:** <branch name>
- **Review iterations:** N
- **Contract deviations:** <bulleted list or "none">
- **Notes:** <any issues or deviations from the plan>

## Integration Review
- **Issues found:** N
- **Issues fixed:** N
- **Contract deviations found:** N
- **Issues needing manual attention:** N
- **Cleanup PR:** <URL or "none">

## Failures and Blocked Features

### <Feature Name> (FAILED)
- **Wave:** N
- **Reason:** <build failure | review loop exhausted | merge conflict | Phase 1 sync timeout | agent timeout>
- **Last error:** <1-2 sentence summary>
- **Rollback tag:** swarm/<slug>/pre-wave-<N>

### <Feature Name> (BLOCKED)
- **Blocked by:** <failed feature name>
- **Transitively blocked by:** <root failed feature name, if chain is longer than one step>
```
