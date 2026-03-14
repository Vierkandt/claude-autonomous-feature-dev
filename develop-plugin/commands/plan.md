---
name: plan
description: "Interactively brainstorm and structure a software platform plan. Runs three phases with approval gates: (A) feature planning with guided questions, (B) convention negotiation producing a project contract, (C) conditional decomposition preview for new projects. Produces docs/plans/<slug>-plan.md, docs/project-contract.md, and optionally docs/workbranches/<slug>/. Run before /swarm."
argument-hint: "[optional: project name or starting topic]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# /plan — Interactive Platform Planning

## Step 1 — Determine starting point

If `$ARGUMENTS` is non-empty, use it as the opening context. Otherwise begin cold.

## Step 2 — Phase A: Feature planning

Ask the three required core questions in sequence. Do not ask them all at once:
1. "What is this platform? Give it a name and describe its purpose in a sentence or two."
2. "What tech stack do you have in mind? (language, framework, database, hosting)"
3. "Where should it be deployed? (Vercel, AWS, self-hosted, Docker, etc.)"

After the three core questions, continue with open-ended exploration:
- What features does the platform need?
- For each feature: what does it do? Who uses it?
- Which features depend on each other?
- Any priorities, constraints, or deadlines?

Ask follow-up questions naturally until the user signals completion (e.g., "that's all," "I think that covers it," "let's move on").

Produce a plan document draft using this format:

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

Display the plan inline.

**Gate:** Display the plan and ask: "Here's the structured plan. Does this look right? Say 'yes' to continue to conventions, or tell me what to change." Do not proceed to Phase B until the user explicitly confirms.

## Step 3 — Phase B: Convention negotiation

After Phase A is confirmed, transition: "Now let's define the shared conventions every agent will follow. These become hard constraints — every auto-dev agent in the swarm will follow them exactly."

Ask about each contract section in sequence. For each, propose a sensible default based on the stack confirmed in Phase A:

- "What does the user model look like? List fields and types." (Or: "Based on your stack, here's a starting User model — does this look right?")
- "REST or GraphQL? What's the base URL pattern? How are errors shaped?"
- "How does auth work? JWT, session cookies, OAuth? Where does the middleware live?"
- "Where do routes, models, middleware, and utilities live in the file structure?"
- "Any shared patterns? Repository pattern, validation library, auth guard wrapper?"

After collecting answers, produce a project contract draft using this format:

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

Display the contract inline.

**Gate:** "Here's the project contract. Review it carefully — every agent in the swarm follows it exactly. Say 'yes' to continue, or correct anything that's wrong." Do not proceed to Phase C until the user explicitly confirms. If the user corrects anything, update the contract and re-display it without re-running Phase A.

## Step 4 — Phase C: Decomposition preview (conditional)

Check whether a source directory exists:

```bash
ls -d src app lib 2>/dev/null | head -1
```

**If a source directory exists (existing project):** Skip Phase C. Tell the user: "This looks like an existing project. Decomposition will happen when you run `/swarm` — the decomposer needs to explore your codebase first to avoid conflicts with existing code. Saving plan and contract now." Jump to Step 5.

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

**Gate:** "Here's how the work will be decomposed. Say 'yes' to save everything, or tell me what to adjust." If the user wants changes, re-run the decomposer with the correction. If the user says the contract is wrong, return to Phase B without re-running Phase A. Each phase is independently revisable.

## Step 5 — Save outputs

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

- Input: optional `$ARGUMENTS` (starting topic string)
- Output files written: `docs/plans/<slug>-plan.md`, `docs/project-contract.md`, optionally `docs/workbranches/<slug>/*.md`
- No git operations, no builds, no PRs

## Dependencies

- Invokes the `decomposer` agent (via Agent tool) during Phase C for new projects only
- May read `docs/project-context.md` if it exists, to orient on existing stack details
