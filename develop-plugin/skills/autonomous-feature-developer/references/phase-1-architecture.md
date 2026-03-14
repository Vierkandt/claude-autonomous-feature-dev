# Phase 1 — Architecture

*Goal: produce a written implementation plan. Do NOT edit source files.*

## Steps

1. **Read the project context file** in full. Note the tech stack, coding conventions, and any referenced design specs.

2. **Read referenced design specs.** If the context file's Design Spec section points to a document, read it now.

3. **Explore the codebase.** Use Glob, Grep, and Read to understand the areas listed in the context file's Key Paths section. Focus on:
   - How existing features are structured (find a representative one and trace it)
   - The data model / schema layer
   - Routing or entry points
   - Shared utilities, base components, or layout wrappers
   - Configuration files (build, framework, linting)

3a. **Read the project contract** (skip this step if `$CONTRACT_FILE` does not exist):

    Read `$CONTRACT_FILE` in full. Every definition in this file is a hard constraint:
    - All shared models must match the contract's field names and types exactly
    - The API shape (base path, error format, pagination) must match
    - File locations must follow the contract's File Structure section exactly
    - Patterns (repository pattern, validation library, auth guard) must be applied
      as the contract defines

    Your architecture plan must be compatible with every constraint in this file.
    If a part of the feature is not covered by the contract, make local decisions freely.

    If the existing codebase contradicts the contract on any point (existing project
    scenario): follow the codebase reality for that point, and note the discrepancy
    in the plan's Architecture Decisions section with the label "CONTRACT DISCREPANCY:".

3b. **Read wave learnings** (skip this step if `$LEARNINGS_FILE` does not exist):

    Read `$LEARNINGS_FILE` in full. Treat every entry as factual ground truth about
    how this specific codebase behaves — more authoritative than the contract for the
    items they cover.

    "Contract corrections" entries supersede the contract for those specific items.
    "Patterns discovered" entries are ground truth about file structure and framework
    behavior. "Build" entries tell you what commands or flags are actually required.

3c. **Incorporate sub-features** (skip this step if `$WORKBRANCH_SUBFEATURES` is empty):

    The WORKBRANCH_SUBFEATURES list is the seed for the Implementation Order section
    of your plan. Map each sub-feature to one or more steps. Every sub-feature in the
    list must appear somewhere in the plan.

    You may:
    - Add additional steps between sub-features as needed
    - Expand a single sub-feature into multiple steps
    - Reorder steps within a sub-feature's scope if codebase exploration reveals
      ordering dependencies

    You may NOT:
    - Skip a listed sub-feature
    - Merge two distinct sub-features into one undifferentiated step

4. **Write the plan** to `$PLAN_FILE` using the template below.

5. **Commit the plan** so it is preserved if the session is interrupted before implementation begins:

   ```bash
   cd "$WORKTREE" && git add -- "$PLAN_FILE" && git commit -m "docs: add implementation plan"
   ```

5a. **Phase 1 sync point** (skip this step if `$PHASE1_SYNC` is not `"true"`):

    Write the sync file to signal that Phase 1 is complete:

    ```bash
    REPORT_FILE="docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-phase1-report.json"
    cat > "$REPORT_FILE" << EOF
    {
      "workbranch": "$WORKBRANCH_SLUG",
      "phase1_complete": true,
      "files_to_create": [<comma-separated quoted paths from "Files to Create" section>],
      "files_to_modify": [<comma-separated quoted paths from "Files to Modify" section>]
    }
    EOF
    ```

    Then poll for the resolution file:

    ```bash
    RESOLUTION_FILE="docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-phase1-resolution.json"
    TIMEOUT=600
    ELAPSED=0
    while [ ! -f "$RESOLUTION_FILE" ]; do
      sleep 30
      ELAPSED=$((ELAPSED + 30))
      if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "ERROR: Phase 1 sync timeout after ${TIMEOUT}s" >&2
        exit 1
      fi
    done
    ```

    Read the resolution file. It contains three fields:
    - `proceed`: always `true` (file existence is the proceed signal)
    - `reassigned_files`: list of file paths reassigned to another workbranch
    - `wait_for`: slug of another workbranch to wait for, or `null`

    Apply the resolution:

    1. For each path in `reassigned_files`: remove it from the plan's Files to Create
       or Files to Modify section. Add a note in Architecture Decisions:
       "FILE REASSIGNED: <path> — assigned to <other-workbranch> by orchestrator."

    2. If `wait_for` is not `null`:
       ```bash
       WAIT_FILE="docs/workbranches/$PLAN_SLUG/$WAIT_FOR-done.json"
       WAIT_TIMEOUT=3600
       WAIT_ELAPSED=0
       while [ ! -f "$WAIT_FILE" ]; do
         sleep 60
         WAIT_ELAPSED=$((WAIT_ELAPSED + 60))
         if [ $WAIT_ELAPSED -ge $WAIT_TIMEOUT ]; then
           echo "ERROR: wait_for timeout — $WAIT_FOR never completed" >&2
           exit 1
         fi
       done
       ```
       After the file appears, read it. If its `status` is `"failed"`, mark this
       workbranch as failed too with reason: "wait_for dependency failed."

    Proceed to Phase 2.

## Plan Template

Include only sections that apply to this feature. Omit inapplicable sections entirely — do not write "None" or "N/A" for each one.

```markdown
# <Feature Title> — Implementation Plan

## Summary
<2-3 sentences: what will be built and why>

## Files to Create
- `path/file` — <purpose>

## Files to Modify
- `path/file` — <what changes and why>

## Architecture Decisions
<Key decisions: new components/modules, data models, APIs, state management, trade-offs>

## Schema / Data Changes
<Migrations, collection schemas, config changes>

## Route / Endpoint / CLI Changes
<New pages, API routes, CLI subcommands, redirects>

## Style / UI Changes
<Theme additions, design tokens, component styling>

## Config / Dependency Changes
<New dependencies, build config, infra, CMS config>

## Implementation Order
1. <step — what to do and which file(s) it touches>
2. <step>
...
```

## Guidelines

- The implementation order matters. Put foundational changes first (schemas, config) and dependent features after.
- Be specific about file paths — the coding agent should not have to guess where things go.
- If the feature touches an existing pattern (e.g. there are already 5 pages that work a certain way), note which existing file to use as a reference.
- If a decision has trade-offs (e.g. "we could use a Preact island or a plain Astro component"), state the choice and why.
- If the project contract (`docs/project-contract.md`) defines a model, API shape, or
  file location relevant to this feature, those definitions are hard constraints. Your
  plan must be compatible with them. Note any incompatibilities you discover in the
  Architecture Decisions section with the label "CONTRACT DISCREPANCY:".
