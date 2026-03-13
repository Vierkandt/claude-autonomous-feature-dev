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

4. **Write the plan** to `$PLAN_FILE` using the template below.

5. **Commit the plan** so it is preserved if the session is interrupted before implementation begins:

   ```bash
   cd "$WORKTREE" && git add -- "$PLAN_FILE" && git commit -m "docs: add implementation plan"
   ```

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
