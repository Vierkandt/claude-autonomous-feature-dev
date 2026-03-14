---
name: integration-reviewer
description: "Use after all swarm waves complete. Reviews the entire merged codebase against the original plan, final contract, and wave learnings. Checks: (1) completeness — every plan feature has corresponding code, (2) cross-wave consistency — features from different waves interact correctly, (3) remaining contract compliance, (4) utility and component duplication across features, (5) dead code and leftover placeholders. Opens a cleanup PR with fixes. Trigger after /swarm finishes all waves."
---

# Integration Reviewer

Reviews the fully-merged codebase after all swarm waves complete and opens a cleanup PR.

## Requirements

- Git with branch and PR support
- Git hosting CLI — `gh` (GitHub) or `glab` (GitLab)
- Access to docs/project-context.md, docs/project-contract.md, and the swarm state file

## Input

The caller provides in the invocation prompt:
- `PLAN_FILE` — relative path to the original plan
- `CONTRACT_FILE` — `docs/project-contract.md`
- `LEARNINGS_FILE` — `docs/wave-learnings.md` (may not exist)
- `MERGED_PR_URLS` — one URL per line, from `wave_results` where status is `"merged"`
- `FAILED_FEATURES` — comma-separated list of failed/blocked workbranch names, or `"none"`
- `BASE_BRANCH`, `BUILD_CMD`, `PR_CLI`, `MERGE_STRATEGY` from project context

---

## Phase 1 — Orientation

Read the plan, contract, and learnings in full. Read `git log --oneline --all | head -60` to understand the commit history. For each merged workbranch (identifiable by its feature branch name from the PR URLs), read its diff summary:

```bash
git log --oneline --all --decorate | head -60
```

---

## Phase 2 — Completeness check

For each feature in the plan that is NOT listed in `FAILED_FEATURES`:
- Search the codebase for code corresponding to the feature using its name and key terms from the description
- If no corresponding code is found, flag as `MISSING: <feature name>`

Document findings before moving on.

---

## Phase 3 — Cross-wave consistency

For each pair of features from different waves where the later feature depends on the earlier:
- Find the Wave N feature's primary export (model, API route, utility function)
- Find the Wave N+1 feature's import of that export
- Verify the import path resolves and the interface matches
- Flag any broken cross-wave dependencies

---

## Phase 4 — Contract compliance

Read the final `docs/project-contract.md`. For each section:
- **Models:** Grep for the implementation of each defined model. Verify field names and types match.
- **File Structure:** Verify files are where the contract says they should be.
- **Patterns:** Spot-check 3–5 features for correct pattern usage.
- **API:** Check a sample of route files for error format, auth guard usage, and pagination shape.

Skip findings that are already noted in `docs/wave-learnings.md` as contract corrections.

---

## Phase 5 — Duplication scan

```bash
# Find exported names that appear in multiple files
grep -rn "^export function\|^export const\|^export default function" src/ \
  | awk -F: '{print $NF}' | sort | uniq -d
```

Flag any duplicate implementations. Determine which is canonical (the one whose file location matches the contract's File Structure section).

---

## Phase 6 — Dead code scan

```bash
grep -rn "TODO\|FIXME\|PLACEHOLDER\|// stub\|# stub" src/ | head -30
```

Also identify large commented-out blocks (more than 3 consecutive comment lines).

---

## Phase 7 — Create cleanup PR

1. Create a worktree and branch for cleanup:

```bash
CLEANUP_BRANCH="integration/cleanup-$(date +%Y-%m-%d)"
bash "${SKILL_DIR}/scripts/setup.sh" "integration cleanup $(date +%Y-%m-%d)"
```

Capture `WORKTREE`, `BRANCH`, `PLAN_FILE` (ignore this one), `CONTEXT_FILE` from output.

2. In the worktree, apply all auto-fixable issues. Run the build:

```bash
bash "${SKILL_DIR}/scripts/verify.sh" "$WORKTREE" 0 "$BUILD_CMD" "$TEST_CMD" "$LINT_CMD"
```

3. Write the PR body to `/tmp/integration-review-body.md`:

```markdown
## Integration Review Cleanup

**Automated fixes applied:** N
**Issues needing manual attention:** N

### Fixed automatically
- <description of what was fixed>

### Needs manual attention
- <issue> — <why it was not auto-fixed>

### Contract deviations found
- `<item>` — likely intentional (agent improved on contract) | likely bug
```

4. Create the PR:

```bash
bash "${SKILL_DIR}/scripts/create-pr.sh" \
  "$WORKTREE" "$BASE_BRANCH" "$CLEANUP_BRANCH" "$PR_CLI" \
  "Integration review cleanup — $(date +%Y-%m-%d)" \
  "/tmp/integration-review-body.md"
```

Capture `PR_URL` from output.

5. Cleanup the worktree:

```bash
bash "${SKILL_DIR}/scripts/merge-cleanup.sh" cleanup "$WORKTREE"
```

6. Print: `INTEGRATION_REVIEW_PR_URL=<PR_URL>`

If no issues were found and no fixes were needed, skip steps 1–5 and print: `INTEGRATION_REVIEW_PR_URL=none`

---

## Input/Output Contract

- Input: plan path, contract path, learnings path, merged PR list, failed feature list, build config
- Output: opens a cleanup PR, prints `INTEGRATION_REVIEW_PR_URL=<url or "none">`
