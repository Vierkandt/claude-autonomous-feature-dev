# Orchestrator Conflict Resolution (exit 1)

The script outputs `CONFLICT_FILES:` followed by one conflicting path per line. For each conflicting file:

1. Read the file at HEAD (current base branch state after prior merges in this queue): `git show HEAD:<file>`
2. Read the file from the feature branch: `git show <branch>:<file>`
3. Read both workbranch files for intent.
4. Read the contract for the canonical version of any model or pattern.

## Resolution rules (apply in order, first match wins)

| File type | Resolution |
|---|---|
| Shared type file (`src/types/*.ts`, similar) | Merge both sets of additions — both features added different exports, keep both |
| Config file (`package.json`, `.env.example`, etc.) | Merge additive changes; for conflicting values, use the base branch version |
| Model/schema file | Use higher-priority workbranch's version (it merged first, it is ground truth). Log the decision in wave learnings. |
| Any other file | If the conflict is purely additive (both add non-overlapping content), merge both. Otherwise, use higher-priority workbranch's version. |
| Unresolvable | Abort rebase: `git rebase --abort`. Record "failed" with error "unresolvable merge conflict in `<file>` — manual resolution required". Continue queue. |

## After applying resolution

```bash
# For each resolved file:
git add -- <file>
git rebase --continue
git push --force-with-lease origin <branch>
# Then proceed with PR merge
```
