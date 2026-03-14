# Phase 3 — Pull Request

*Goal: PR/MR opened with a clear, reviewable description.*

## Steps

1. **Gather context** for the PR body:

   ```bash
   git -C "$WORKTREE" log ${BASE_BRANCH}..${BRANCH} --oneline
   git -C "$WORKTREE" diff --name-only ${BASE_BRANCH}..${BRANCH}
   ```

2. **Write the PR body** to a temporary file (e.g. `/tmp/pr-body.md`). Structure:

   ```markdown
   ## Summary

   - <bullet points from the plan's Summary section>

   ## Changes

   - `path/file` — <one-line description>
   - `path/file` — <one-line description>
   ...

   ## Test Plan

   - [ ] Build passes (`<BUILD_CMD>`)
   - [ ] Tests pass (`<TEST_CMD>`)          ← omit if no test command
   - [ ] Lint passes (`<LINT_CMD>`)          ← omit if no lint command
   - [ ] <feature-specific manual check>
   - [ ] <another feature-specific check>
   ...

   ## Known Issues                            ← omit section if none

   - <description of any unresolved build/test failure from Phase 2>
   ```

3. **Create the PR** using the script:

   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/create-pr.sh" \
     "$WORKTREE" \
     "$BASE_BRANCH" \
     "$BRANCH" \
     "$PR_CLI" \
     "<title>" \
     "/tmp/pr-body.md"
   ```

4. **Capture the output.** The script prints `PR_URL=...` and `PR_NUMBER=...`. Store both for Phase 4.

## Guidelines

- The PR title should be a concise description of the feature, not the slug. E.g. "Add dark mode toggle" not "feature/add-dark-mode-toggle."
- The test plan should include at least one feature-specific verification step beyond "build passes." Think about what a reviewer would manually check.
- If Phase 2 had known issues, be upfront about them in the PR body. Don't hide failures.
