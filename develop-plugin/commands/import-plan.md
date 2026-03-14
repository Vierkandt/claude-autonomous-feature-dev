---
name: import-plan
description: "Parse a brainstorm document (exported from Claude.ai or any source) into a structured plan and project contract. Accepts a file path or inline pasted text as the argument. Always presents drafts for confirmation before writing — never silently infers conventions. Usage: /import-plan <file-path>  OR  /import-plan <pasted brainstorm text>"
argument-hint: "<file-path or pasted brainstorm text>"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# /import-plan — Parse Brainstorm into Structured Plan

## Step 1 — Resolve input

If `$ARGUMENTS` is empty: ask "Please paste your brainstorm text or provide a file path."

If `$ARGUMENTS` looks like a file path (contains `/` or `.md` extension): check whether it exists with `[ -f "$ARGUMENTS" ]`. If yes, read it. If no, treat `$ARGUMENTS` as inline text.

Otherwise treat `$ARGUMENTS` as the raw brainstorm text.

## Step 2 — Extract features

Parse the input text using best-effort inference. Look for:
- Numbered lists, bullet points, or headings that describe features
- Phrases like "users can...", "the system should...", "we need..."
- Dependency hints: "requires X", "needs X to be done first", "after X", "depends on X"
- Priority hints: "core feature", "critical", "must have", "nice to have", "later", "v2"
- Stack information: framework names, database names, hosting names

Build a structured feature list from everything found.

## Step 3 — Present plan draft

Display the extracted plan in this canonical format:

```markdown
# <Platform Name>

## Overview
<2-3 sentences: what the platform does and who it's for>

## Stack
<Language, framework, database, hosting — or "see project-context.md">

## Deployment
<Where and how: Vercel, AWS, self-hosted, Docker, etc.>

## Features

### Feature: <Name>
Description: <What this feature does, in natural language>
Dependencies: <comma-separated feature names exactly as written, or "none">
Priority: <high | medium | low>

### Feature: <Name>
Description: ...
Dependencies: ...
Priority: ...
```

Lead with: "I found N features. Here's the structured plan:"

**Gate:** "Does this look right? Any features missing, misnamed, or with wrong dependencies?" Wait for explicit confirmation. Accept corrections and re-display. Do not proceed until the user says "yes" or equivalent affirmation.

## Step 4 — Infer conventions

From the brainstorm text, identify any mentioned conventions: specific model names and fields, API patterns, framework choices, file structure mentions.

## Step 5 — Present contract draft

Display the inferred contract draft in this canonical format:

```markdown
# Project Contract

> This file is read by every auto-dev agent in the swarm.
> It contains hard constraints. Every agent follows every rule here exactly.

---

## Models

<TypeScript interfaces or equivalent for every shared data model>

---

## API

- Style: <REST | GraphQL>
- Base path: <e.g. /api/v1>
- Auth mechanism: <e.g. JWT in httpOnly cookie>
- Auth middleware location: <path>
- Error shape: <e.g. `{ error: string, code: number }`>
- Pagination: <e.g. `{ data: T[], nextCursor: string | null }`>

---

## File Structure

- Routes: <path pattern>
- Models: <path pattern>
- Middleware: <path pattern>
- Utils: <path pattern>
- Shared types: <path pattern>

---

## Patterns

- Database access: <pattern>
- Validation: <approach>
- Auth guard: <approach>
- Type exports: <approach>

---

## Dependencies

- <shared dependency with version constraint>
```

Lead with: "Based on the brainstorm, here's a draft project contract:"

Prominently warn: "Review this carefully. Every auto-dev agent in the swarm will follow it exactly. Do not approve a contract that contains guesses you have not verified."

**Gate:** Wait for explicit user confirmation or corrections. Apply corrections, re-display. Do not proceed until explicitly approved. If the user approves technical details with only a vague "looks good," ask them to specifically confirm the model fields and API patterns before continuing.

## Step 6 — Decomposition preview (conditional)

Check whether a source directory exists:

```bash
ls -d src app lib 2>/dev/null | head -1
```

**If a source directory exists (existing project):** Skip decomposition. Tell the user: "This looks like an existing project. Decomposition will happen when you run `/swarm` — the decomposer needs to explore your codebase first to avoid conflicts with existing code. Saving plan and contract now." Jump to Step 7.

**If no source directory exists (new project):** Invoke the `decomposer` agent via the Agent tool. Provide the plan content, contract content, plan slug, and `is_existing_project: false`.

After the decomposer completes (it will have written workbranch files), display a wave execution preview:

```
Wave execution plan:

Wave 1 (parallel): <workbranch names>
Wave 2 (parallel): <workbranch names>
...

Merge order within each wave: <priority order>
Total: N workbranches across N waves.
```

**Gate:** "Here's how the work will be decomposed. Say 'yes' to save everything, or tell me what to adjust." If the user wants changes, re-run the decomposer with the correction. If the user says the contract is wrong, return to Step 5 without re-running earlier steps. Each phase is independently revisable.

## Step 7 — Save outputs

Derive `<slug>` from the platform name: lowercase, non-alphanumeric characters become hyphens, collapse consecutive hyphens, strip leading/trailing hyphens, truncate to 50 characters.

```bash
mkdir -p docs/plans docs/workbranches docs/reports
```

Write the plan to `docs/plans/<slug>-plan.md`.

Write the contract to `docs/project-contract.md`. If the file already exists, warn the user before overwriting: "docs/project-contract.md already exists. Overwriting it — backing up the previous contract to docs/project-contract.backup.md first." Copy the existing file to `docs/project-contract.backup.md` before writing the new one.

For new projects only: the decomposer has already written workbranch files to `docs/workbranches/<slug>/`.

Confirm to the user:

```
Plan saved:     docs/plans/<slug>-plan.md
Contract saved: docs/project-contract.md
Workbranches:   docs/workbranches/<slug>/ (N files)  [new projects only]

Next step: /swarm docs/plans/<slug>-plan.md
```

## Input/output contract

- Input: `$ARGUMENTS` — file path or raw brainstorm text (required, but ask if empty)
- Output files written: `docs/plans/<slug>-plan.md`, `docs/project-contract.md`, optionally `docs/workbranches/<slug>/*.md`
- No git operations, no builds, no PRs

## Dependencies

- Invokes `decomposer` agent during Step 6 for new projects
