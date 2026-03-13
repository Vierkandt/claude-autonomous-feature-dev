# Phase 2 — Implementation

*Goal: working code that passes build, tests, and lint.*

## Steps

1. **Read the plan** (`$WORKTREE/$PLAN_FILE`) in full before writing any code.

2. **Implement** every item in the plan's Implementation Order, following the coding conventions from the project context file.

   Key things to check against the context file as you code:
   - Language and typing rules (strict types, no `any`, interfaces vs. types)
   - Import/export conventions
   - Component patterns (which kind for static vs. interactive)
   - Styling approach (utility classes, tokens, responsive breakpoints)
   - Performance constraints (JS budget, lazy loading, SSR/SSG)
   - Accessibility requirements (semantic HTML, ARIA, alt text)
   - User-facing language (Dutch, English, etc.)

3. **Verify** using the verify script. Run it in single-attempt mode first to see where things stand:

   ```bash
   bash "$SKILL_DIR/scripts/verify.sh" "$WORKTREE" 0 "$BUILD_CMD" "$TEST_CMD" "$LINT_CMD"
   ```

   If any step fails, read the error output, fix the code, and re-run. The script prints the last 20 lines of output for each failure to help diagnosis.

4. **Retry cap.** If you've attempted fixes 5 times for the same failing step and it still won't pass, stop. Commit what you have and note the failure — it will be reported in the PR description under "Known issues."

5. **Commit** once verification passes (or after hitting the retry cap):

   ```bash
   cd "$WORKTREE" && git add -- <list every specific file you created or modified> && git commit -m "feat: <one-line summary>"
   ```

   Never use `git add -A` or `git add .` — list paths explicitly to avoid accidentally committing temp files, generated artifacts, or sensitive files.

## Guidelines

- Implement in the order the plan specifies. Earlier steps often create foundations later steps depend on.
- If the plan references an existing file as a pattern to follow, read that file before writing the new one.
- If you discover the plan is wrong or incomplete mid-implementation (e.g. a missing dependency, an overlooked edge case), fix the code to be correct rather than blindly following the plan. Add a note in the commit message about the deviation.
- Do NOT edit files outside `$WORKTREE`.
