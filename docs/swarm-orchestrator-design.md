# Swarm Orchestrator — Design Document

**Status:** Design complete, pending implementation planning
**Date:** 2026-03-14

---

## Vision

A user brainstorms a software platform idea (in the Claude app or interactively in Claude Code), produces a single plan document, and the plugin autonomously decomposes it into features, builds a dependency graph, and dispatches a swarm of parallel agents — each running the existing auto-dev pipeline in its own git worktree. After all features merge, an integration review catches cross-feature issues and opens a cleanup PR.

The entire process is fully autonomous: launch, walk away, get a final report.

---

## Decisions

| Question | Decision |
|---|---|
| Plan input format | Simple markdown — natural language feature descriptions |
| Plan source | Both: accept an existing plan file OR generate one interactively via `/plan` |
| Plan import | Separate `/import-plan` command for pasting brainstorm output from Claude app |
| Feature granularity | Two-level: coarse workbranches containing ordered sub-features |
| Agent guidance level | **C-lite** — sub-features + project contract. Agents do full Phase 1 exploration but follow shared contracts for models, APIs, patterns |
| Coordination mechanism | Two-file approach: `project-context.md` (broad orientation) + `project-contract.md` (precise shared conventions) |
| Contract lifecycle | Living document — self-corrects after each wave via wave-transition agent. Updates are additive/corrective only. |
| Dependency handling | Explicit in the plan document; plugin respects topological ordering |
| Parallelism | Independent features run in parallel; dependent features wait for prerequisites. All agents in a wave must finish before merging begins. |
| Same-wave merge strategy | Sequential merge queue with rebase; priority determines merge order; file ownership prevents conflicts |
| Failure handling | Fail only the dependency chain; unrelated features continue. Halt if failures transitively block >50% of remaining features. |
| Rollback strategy | Git tags per wave (`swarm/<slug>/pre-wave-N`, `post-wave-N`); revert via `git revert`, not `git reset --hard` |
| User control during execution | Fully autonomous — no checkpoints, final report only |
| Integration timing | Per-wave transition (single agent: micro-review + contract validation + knowledge extraction) + final integration review |
| Cross-wave learning | Shared `docs/wave-learnings.md` file, appended after each wave, read by all subsequent agents |
| `/plan` interaction style | Three-phase with approval gates: feature planning → convention negotiation → decomposition preview |
| `/plan` Phase C timing | Conditional: new projects decompose at `/plan` time; existing projects decompose at `/swarm` time with codebase awareness |
| `/import-plan` behavior | Always infer draft, always present for confirmation. Never silently write conventions. |
| Decomposition staleness | `/swarm` checks plan modification time vs workbranch files; re-decomposes if plan is newer |
| File ownership timing | Predicted at decomposition, finalized after Phase 1 sync point within each wave |
| Partial re-runs | Swarm state file tracks wave progress; `/swarm` offers resume on re-invocation |
| Final report | Terminal summary + written report committed to repo |
| Agent vs command behavior | Agent is the "ops layer" — handles ambiguity, runtime adaptation, post-run analysis. Commands are strict and scriptable. |
| Architecture | Hybrid: commands for explicit control + agent for natural language |
| Relationship to existing plugin | Evolution — add alongside existing `/auto-dev` and `/init` |

---

## Architecture

### Commands

| Command | Purpose | Input | Output |
|---|---|---|---|
| `/init` | Set up project for auto-dev | — | `.claude/settings.local.json`, `docs/project-context.md` |
| `/auto-dev` | Build a single feature end-to-end | Feature description or workbranch file | Merged PR |
| `/plan` | Interactive brainstorming → structured plan + project contract | Conversation (3 phases with approval gates) | Plan at `docs/plans/<name>-plan.md`, contract at `docs/project-contract.md` |
| `/import-plan` | Parse brainstorm output into structured plan + project contract | Raw text or file path | Plan at `docs/plans/<name>-plan.md`, contract at `docs/project-contract.md` |
| `/swarm` | Decompose plan → dispatch parallel agents → integrate | Plan file path | Report + all PRs merged + integration PR |

### Agents

| Agent | Purpose |
|---|---|
| `swarm-orchestrator` | Operations intelligence layer — pre-launch, runtime adaptation, post-run analysis, conflict resolution |
| `decomposer` | Break plan features into workbranches and sub-features with file ownership |
| `wave-transition` | Single-pass post-wave agent: micro-review + contract validation + knowledge extraction |

### Skills

| Skill | Purpose |
|---|---|
| `autonomous-feature-developer` | Per-feature pipeline (existing) |
| `integration-reviewer` | Final post-merge cross-feature review against original plan + contract |

---

## Two-File Coordination: Context vs Contract

Every auto-dev agent reads both files. They serve different purposes.

### `docs/project-context.md` — Broad orientation (existing)

Written by `/init`. Human-friendly. Covers:
- Stack, framework, hosting
- Build, test, lint commands
- Key paths and directory overview
- Coding style preferences (naming, imports, exports)
- Git/PR conventions

**Audience:** Human setting up a project + agents needing general orientation.
**Lifespan:** Once per project, rarely changes.

### `docs/project-contract.md` — Precise shared conventions (new)

Generated by `/plan` or `/import-plan` during the conventions phase. Agent-optimized. Covers:

```markdown
# Project Contract

## Models

\`\`\`typescript
interface User {
  id: string           // uuid
  email: string        // unique
  name: string
  createdAt: Date
}

interface Organization {
  id: string           // uuid
  name: string
  ownerId: string      // references User.id
}
\`\`\`

## API

- Style: REST
- Base: /api/v1
- Auth: JWT in httpOnly cookie, middleware at src/middleware/auth.ts
- Errors: { error: string, code: number }
- Pagination: cursor-based { data: T[], nextCursor: string | null }

## File Structure

- Routes: src/routes/<resource>.ts (one file per resource)
- Models: src/models/<name>.ts (Prisma schema + Zod validators)
- Middleware: src/middleware/<name>.ts
- Utils: src/lib/<name>.ts

## Patterns

- Database: repository pattern, src/repositories/<model>.ts
- Validation: Zod schema co-located with route, exported as <Resource>Schema
- Auth guard: wrap route with requireAuth() middleware
- Shared types: src/types/<domain>.ts, re-exported from src/types/index.ts
```

**Audience:** Auto-dev agents only. No prose, no optionality, no examples.
**Key property:** Complete and unambiguous. If a section doesn't apply, it's omitted entirely — no "N/A" or "optional" markers.

### Contract as a living document

The contract self-corrects after each wave via the wave-transition agent:

1. `/plan` or `/import-plan` generates the initial contract from the brainstorm
2. After each wave merges, the wave-transition agent checks actual code against the contract
3. Minor deviations (extra fields, adjusted paths) are auto-corrected in the contract
4. Major deviations are logged as warnings
5. Subsequent wave agents read the updated contract

**Key constraint:** Contract updates are additive/corrective only. You can add a field to a model or change a file path, but you cannot remove a model that a previous wave already implemented.

Wave 1 should include the most foundational features — auth, data models, core config — because they test the contract most aggressively.

### Contract self-consistency validation

Before the swarm starts, `/swarm` validates that the contract is internally consistent:
- All model references resolve to defined models
- File structure paths are consistent with patterns section
- API endpoints reference existing model fields
- No contradictions between sections

If validation fails, the swarm does not start and reports the specific inconsistencies.

### How agents use them

1. Phase 0 (setup): `setup.sh` validates that both files exist
2. Phase 1 (architecture): agent reads both. Context for orientation, contract for hard constraints. The agent's architecture plan must be compatible with the contract.
3. Phase 2 (implementation): agent follows contract for all shared concerns (models, API shape, file locations). Free to make local decisions for everything else.
4. Phase 4 (review): self-review checks compliance with contract

### How the integration reviewer uses them

The reviewer receives the contract and checks:
- Every model in the contract exists in the codebase with the correct shape
- Every pattern in the contract is followed consistently across all features
- Deviations are flagged — some may be legitimate (agent found a better approach), some may be bugs

---

## Pipeline

```
                    ┌──────────────┐     ┌────────────────┐
                    │   /plan      │     │ /import-plan   │
                    │ (3 phases    │     │ (draft +       │
                    │  w/ gates)   │     │  confirm)      │
                    └──────┬───────┘     └───────┬────────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────────────────────┐
                    │  Plan document               │
                    │  docs/plans/<name>-plan.md    │
                    │  +                           │
                    │  Project contract            │
                    │  docs/project-contract.md     │
                    └──────────────┬───────────────┘
                                  │
                          /swarm  │  (or swarm-orchestrator agent)
                                  ▼
                    ┌──────────────────────────────┐
                    │  1. Validate                 │
                    │     - Plan: no circular deps │
                    │     - Contract: exists +     │
                    │       self-consistent        │
                    │     - Context: exists         │
                    │     - Staleness check:        │
                    │       re-decompose if plan    │
                    │       newer than workbranches │
                    └──────────────┬───────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │  2. Decompose (agent)         │
                    │     - Parse plan → workbranch │
                    │       files with sub-features │
                    │     - Assign predicted file   │
                    │       ownership               │
                    │     - Flag ownership conflicts │
                    │     - For existing projects:  │
                    │       explore codebase first  │
                    └──────────────┬───────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │  3. Dependency graph          │
                    │     Topological sort →        │
                    │     wave assignment           │
                    └──────────────┬───────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │  4. Wave execution loop       │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │ Tag: pre-wave-N        │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Dispatch auto-dev      │  │
                    │  │ agents (parallel)      │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Phase 1 sync point     │  │
                    │  │ Wait for all agents to │  │
                    │  │ complete Phase 1, then  │  │
                    │  │ finalize file ownership │  │
                    │  │ from actual arch plans  │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Agents continue        │  │
                    │  │ Phase 2-5 (parallel)   │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Wait for ALL agents    │  │
                    │  │ to finish              │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Sequential merge queue │  │
                    │  │ (priority order,       │  │
                    │  │  rebase between each)  │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Tag: post-wave-N       │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Wave-transition agent  │  │
                    │  │ (single pass):         │  │
                    │  │  - Micro-review        │  │
                    │  │  - Contract validation │  │
                    │  │  - Knowledge extraction│  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Halt check:            │  │
                    │  │ Do failures block >50% │  │
                    │  │ of remaining features? │  │
                    │  └───────────┬────────────┘  │
                    │              │               │
                    │         Next wave?           │
                    │         ▼ yes    ▼ no        │
                    │       (loop)   (exit)        │
                    └──────────────┬───────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │  5. Final integration review  │
                    │     - Completeness vs plan   │
                    │     - Cross-wave consistency  │
                    │     - Remaining contract      │
                    │       deviations             │
                    │     - Cleanup PR             │
                    └──────────────┬───────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │  6. Final report              │
                    │     - Terminal summary       │
                    │     - Written to             │
                    │       docs/reports/          │
                    │       swarm-<date>-report.md │
                    └─────────────────────────────┘
```

---

## Feature Granularity: Two-Level Hierarchy

Features are decomposed at two levels:

### Level 1 — Workbranches (parallel across agents)

Coarse features that each get their own worktree, auto-dev agent, and PR. Dependencies between workbranches determine wave ordering.

### Level 2 — Sub-features (sequential within an agent)

Ordered implementation steps within a workbranch. These become the Implementation Order in the auto-dev agent's Phase 1 architecture plan. Each sub-feature is a logical commit within the branch.

```
Wave 1
├── Workbranch: User Authentication (one worktree, one PR)
│   ├── Sub-feature: Data model + migrations
│   ├── Sub-feature: Signup flow
│   ├── Sub-feature: Login flow
│   ├── Sub-feature: Password reset
│   └── Sub-feature: Session middleware
│
├── Workbranch: Config & Environment (one worktree, one PR)
│   ├── Sub-feature: Env loading + validation
│   └── Sub-feature: Feature flags
```

### What each level determines

| Concern | Workbranch (L1) | Sub-feature (L2) |
|---|---|---|
| Defined by | Decomposer agent | Decomposer agent |
| Executed by | Auto-dev agent (one per workbranch) | Same agent, sequentially |
| Isolation | Own worktree + branch | Shared branch, logical commits |
| Dependencies | Explicit, cross-workbranch | Implicit, ordered within workbranch |
| Output | One PR | One or more commits within the PR |

---

## Decomposer Agent

The decomposer is an LLM reasoning agent, not a parser. It receives the plan document and produces workbranch files with sub-features.

### Codebase awareness

The decomposer behaves differently based on project state:

- **New project** (no existing `src/` or equivalent): Decompose based on the plan and contract alone. File ownership is assigned from the contract's File Structure section. Can run at `/plan` Phase C time.
- **Existing project**: Explore the codebase first — read directory structure, existing models, routing patterns. Decompose with awareness of what already exists. Must run at `/swarm` time, not `/plan` time. `/plan` Phase C is skipped; `/swarm` handles decomposition with full codebase context.

### Sub-feature decomposition rules

```
You are a feature decomposer. Given a feature description from a plan,
break it into an ordered list of sub-features.

Rules:
1. Each sub-feature must be implementable in a single coding session
   (roughly: touches 1-5 files, produces one logical commit)
2. Sub-features are ordered by dependency — foundations first
3. The first sub-feature should always be data model / schema
   if the feature needs persistent data
4. The last sub-feature should be integration / wiring
   (connecting the pieces to the rest of the app)
5. Each sub-feature gets a one-line description that answers:
   "what files will this touch and what will they do?"

Heuristics for splitting:
- Separate data layer from business logic from UI/API
- Separate read paths from write paths
- Separate auth/middleware from feature logic
- If a description contains "and" connecting distinct concerns, split there
- If a sub-feature would touch more than 5 files, split further

Do NOT:
- Create sub-features smaller than one file change
- Create sub-features that are just "write tests" — tests are part
  of each sub-feature
- Specify architecture decisions — that's the auto-dev agent's job
```

### Workbranch boundary heuristics

The decomposer also decides whether a feature stays as one workbranch or splits:

```
A workbranch should split when:
- It has sub-features that could independently merge without the others
  (e.g., "Auth Backend" vs "Auth UI" — backend can merge and be useful alone)
- It would produce more than ~8 sub-features (too large for one agent session)
- It spans two distinct layers that other features depend on independently
  (e.g., dashboard depends on auth middleware but not auth UI)

A workbranch should NOT split when:
- Sub-features are tightly coupled (changing one requires changing another)
- The feature is already small (3-4 sub-features)
- Splitting would create circular dependencies
```

### File ownership assignment

During decomposition, the agent assigns a **predicted** `Owns` section to each workbranch listing the files/directories it expects to create or modify.

Ownership is **finalized** during the Phase 1 sync point within each wave (see Wave Execution). After all agents in a wave complete Phase 1 (architecture planning), the orchestrator collects actual file lists from each agent's plan, checks for conflicts, and resolves them before Phase 2 begins.

If two workbranches in the same wave claim the same file at decomposition time, the decomposer either:
1. Reassigns the overlapping file to one workbranch
2. Moves one workbranch to a later wave to avoid conflicts

---

## Phase 1 Sync Point

Within each wave, there is a synchronization point between Phase 1 (architecture) and Phase 2 (implementation):

```
All agents in wave complete Phase 1 (architecture plans written)
    │
    ▼
Orchestrator collects actual file lists from each agent's plan
    │
    ▼
Check for ownership conflicts:
  - Two agents plan to create/modify the same file?
  - Predicted ownership differs from actual plan?
    │
    ▼
Conflicts found?
  - None → all agents proceed to Phase 2
  - Conflicts → reassign files or sequence conflicting agents
    (one proceeds to Phase 2 first, the other waits)
```

This ensures file ownership reflects the agent's actual architecture decisions, not the decomposer's predictions. The cost is a brief pause between Phase 1 and Phase 2 while waiting for all agents to complete their plans.

---

## Same-Wave Merge Strategy

When multiple PRs in the same wave are ready to merge, all agents must finish before merging begins. PRs are then merged sequentially, not simultaneously.

### Sequential merge queue

```
All Wave N agents finish
    │
    ▼
Merge queue (by priority, highest first):
  1. Merge auth PR (squash)
  2. Rebase config PR onto updated base → merge (squash)
  3. Rebase logging PR onto updated base → merge (squash)
```

Each PR is rebased onto the latest base before merging. Higher-priority features merge first, making their code the "ground truth" that lower-priority features rebase onto.

### Conflict resolution

If a rebase produces conflicts, the swarm-orchestrator handles resolution directly (not a separate agent):

```
Conflict resolution:
  - Read the conflicting files
  - Read both PRs' intent from their workbranch files
  - Resolve conflicts favoring the contract's conventions
  - If unresolvable automatically, mark the PR as failed
    (don't produce bad merges)
```

---

## Wave-Transition Agent

A single agent that runs one pass over the merged codebase after each wave. Replaces the previous three separate agents (micro-reviewer, contract-validator, knowledge-extractor) to avoid redundant codebase reads and overlapping checks.

### Single-pass outputs

The wave-transition agent reads the merged diffs once and produces three outputs:

**1. Micro-review report:**
- Contract compliance: do merged files follow the contract's file structure, model shapes, API patterns?
- Conflict scan: duplicate utilities, conflicting exports, naming collisions across wave features?
- Build health: does the base branch build pass after all merges?
- Resolution: no issues → proceed; minor → auto-fix and commit; major → fix, log warning

**2. Contract updates:**
- Diff actual code against contract sections
- Minor deviations (extra fields, adjusted paths) → auto-update contract
- Major deviations (wrong pattern, different auth approach) → update contract, log warning
- All updates are additive/corrective only

**3. Wave learnings:**
- Build quirks discovered during this wave
- ORM/framework behaviors
- File structure realities vs expectations
- Dependency notes
- Contract corrections made

Learnings are appended to `docs/wave-learnings.md` under a `## Wave N` heading.

### Learnings format

```markdown
# Wave Learnings

## Wave 1

### Build
- Vite requires explicit .tsx extension in dynamic imports
- `npm run build` must be run from project root, not src/

### Dependencies
- Zod 3.23+ required (earlier versions lack .pipe())
- Prisma client must be regenerated after schema changes: npx prisma generate

### Patterns discovered
- Framework puts middleware in src/middleware/, not src/lib/middleware/
- Auth token is in req.headers.authorization, not req.cookies

### Contract corrections
- User model: added `role: string` field (required by auth middleware)
- File structure: src/utils/ not src/lib/ for project utilities
```

Every auto-dev agent in Wave 2+ reads this file alongside the project context and contract. It is append-only — waves never edit previous waves' learnings.

---

## Decomposition Staleness Detection

When `/swarm` is invoked and workbranch files already exist:

1. Compare the plan file's modification time against the workbranch files' modification times
2. If the plan is newer → re-decompose and warn: "Plan was modified since last decomposition. Re-decomposing."
3. If the plan is older or same → use existing workbranch files

This prevents stale decompositions after the user manually edits the plan between `/plan` and `/swarm`.

---

## Swarm State and Partial Re-Runs

`/swarm` maintains a state file at `docs/workbranches/<slug>/swarm-state.json`:

```json
{
  "plan": "docs/plans/my-plan.md",
  "contract_hash": "abc123",
  "waves_completed": [1, 2],
  "wave_results": {
    "1": {
      "auth": "merged",
      "config": "merged"
    },
    "2": {
      "dashboard": "merged",
      "billing": "failed"
    }
  },
  "current_wave": 3,
  "status": "halted",
  "halt_reason": "billing failure blocks >50% of remaining features",
  "tags": [
    "swarm/my-plan/pre-wave-1",
    "swarm/my-plan/post-wave-1",
    "swarm/my-plan/pre-wave-2",
    "swarm/my-plan/post-wave-2"
  ]
}
```

On re-invocation, `/swarm` detects the state file and offers: "Previous swarm halted at Wave 3. Resume from Wave 3 or start fresh?"

If resuming:
- Skip validation and decomposition (already done)
- Skip completed waves
- Start from `current_wave`
- Failed features from previous waves remain failed; their dependents remain blocked

---

## Rollback Strategy

Each wave creates git tags before and after merging, providing clean rollback points.

### Tags

```bash
git tag swarm/<slug>/pre-wave-1    # Before Wave 1 agents start
git tag swarm/<slug>/post-wave-1   # After Wave 1 PRs merge
git tag swarm/<slug>/pre-wave-2    # Before Wave 2 agents start
git tag swarm/<slug>/post-wave-2   # After Wave 2 PRs merge
# ... and so on
```

### Halt condition

The swarm halts when failures transitively block more than 50% of remaining (not yet completed) features:

1. If ALL features in a wave fail → halt
2. Calculate: of all features not yet merged, how many are now transitively blocked by failures?
3. If blocked > 50% of remaining → halt and suggest rollback
4. Otherwise → continue, log warnings

This avoids both the false positive (halting over one optional feature failing) and the false negative (continuing when most of the plan is unreachable).

### Revert mechanism

Uses `git revert` (not `git reset --hard`, which is in the deny list) to create a new commit that undoes changes. Safe and auditable:

```bash
git revert --no-commit swarm/<slug>/post-wave-(N-1)..HEAD
git commit -m "revert: roll back to post-wave-(N-1)"
```

---

## Failure Handling

When a feature fails (build won't pass, review loop exhausted, PR can't merge):

1. Mark the feature as **failed** in the swarm state
2. Mark all features that depend on it (transitively) as **blocked**
3. Continue executing features in the current and future waves that are NOT in the failed dependency chain
4. Check halt condition: do failures now block >50% of remaining features?
5. Include all failures and blocked features in the final report with reasons

Example:
```
Wave 1: auth (FAILED), config (OK)
Wave 2: dashboard (BLOCKED — depends on auth), billing (OK — depends on config only)
Wave 3: analytics (BLOCKED — depends on dashboard)

Remaining after Wave 1: dashboard, billing, analytics (3 features)
Blocked: dashboard, analytics (2 features = 67% of remaining)
→ HALT: >50% blocked. Suggest rollback to pre-wave-1.
```

---

## Plan Document Format

Produced by `/plan` or `/import-plan`. Input to `/swarm`.

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
Dependencies: <comma-separated feature names, or "none">
Priority: <high | medium | low>

### Feature: <Name>
Description: ...
Dependencies: ...
Priority: ...

...
```

### Rules
- Feature names must be unique within the plan
- Dependencies reference other feature names exactly as written
- Circular dependencies are rejected with an error
- Priority is informational — wave ordering is determined by dependencies, not priority
- Priority is used as a tiebreaker: merge order within waves AND queuing when agent slots are limited

---

## `/plan` Command Behavior

Three phases with user approval gates between each.

### Phase A — Feature planning

**Guided core questions (always asked):**
1. What is this platform? (name and purpose)
2. What tech stack do you have in mind?
3. Where should it be deployed?

**Free-form exploration:**
- What features does it need?
- For each feature, what does it do?
- Which features depend on each other?
- Any constraints, deadlines, or priorities?

The agent asks follow-up questions naturally until the user signals they're done.

**Output:** Plan document draft.
**Gate:** User confirms plan before proceeding.

### Phase B — Convention negotiation

Once features are understood, ask about shared conventions:
- What does the user model look like? Any other shared models?
- REST or GraphQL? API naming conventions?
- How should auth work?
- What's the file/directory structure?
- Any shared patterns (repository pattern, middleware, validation)?

**Output:** Project contract draft.
**Gate:** User confirms contract before proceeding.

### Phase C — Decomposition preview (conditional)

**New project (no existing `src/`):** The decomposer agent breaks features into workbranches with sub-features, assigns dependencies and waves, assigns predicted file ownership, and checks for ownership conflicts.

**Existing project:** Phase C is skipped. Decomposition happens at `/swarm` time when the decomposer can explore the existing codebase. The user is told: "Decomposition will happen when you run `/swarm` — the decomposer needs to explore your existing codebase first."

**Output:** Wave execution preview (which features in which waves, parallelism, merge order).
**Gate:** User confirms decomposition before saving (new projects only).

### Final output
1. Writes the plan to `docs/plans/<slug>-plan.md`
2. Generates the project contract at `docs/project-contract.md`
3. Saves workbranch files to `docs/workbranches/<slug>/` (new projects only)

If the user says "the contract looks wrong," fix it without redoing Phase A. If the decomposition is wrong, fix it without redoing Phase B. Each phase is independently revisable.

---

## `/import-plan` Command Behavior

Accepts either:
- A file path: `/import-plan docs/brainstorm-export.md`
- Inline text: `/import-plan <pasted content>`

Follows a strict protocol — never silently writes conventions:

```
1. Parse input text
2. Extract features (best effort)
3. Infer dependencies from feature descriptions (best effort)
4. Present extracted plan to user:
   "I found N features. Here's the structured plan:"
   [plan preview]
   "Does this look right? Any features missing or dependencies wrong?"
5. User confirms or corrects
6. Infer conventions from the brainstorm text
7. Present draft contract to user:
   "Based on the brainstorm, here's a draft project contract:"
   [contract preview]
   "Review this carefully — every agent will follow it."
8. User confirms or corrects
9. Run decomposition preview (same as /plan Phase C — conditional on project state)
10. User confirms (if applicable)
11. Save all files
```

The contract is too important for inference without confirmation. The plan can tolerate minor inference errors (the user will catch them in the preview), but the contract must be explicitly approved.

---

## `/swarm` Command Behavior

Strict and scriptable:
```
/swarm docs/plans/my-platform-plan.md
```

1. **Check for existing swarm state.** If `swarm-state.json` exists: "Previous swarm halted at Wave N. Resume from Wave N or start fresh?"
2. **Validate** the plan (no circular deps, all referenced deps exist)
3. **Validate contract** exists and is self-consistent (model references resolve, file paths consistent, no contradictions)
4. **Validate** `docs/project-context.md` exists
5. **Staleness check:** if workbranch files exist but plan is newer, re-decompose
6. **Decompose** (if needed) — for existing projects this is the first decomposition; decomposer explores codebase first
7. Build dependency graph, assign waves
8. Print the execution plan (waves, parallelism, merge order)
9. **For each wave:**
   a. Tag `swarm/<slug>/pre-wave-N`
   b. Dispatch auto-dev agents per workbranch (parallel)
   c. **Phase 1 sync point:** wait for all agents to complete Phase 1, finalize file ownership, check for conflicts
   d. Agents continue Phase 2-5 (parallel)
   e. Wait for ALL agents in wave to finish
   f. Run sequential merge queue (priority order, rebase between each; orchestrator resolves conflicts)
   g. Tag `swarm/<slug>/post-wave-N`
   h. Run wave-transition agent (micro-review + contract validation + knowledge extraction)
   i. Update swarm state file
   j. Check halt condition (failures block >50% of remaining → halt + suggest rollback)
10. Run final integration review
11. Write report to `docs/reports/swarm-<date>-report.md`
12. Print terminal summary

---

## Swarm-Orchestrator Agent — The Ops Layer

The agent is not a thin wrapper around `/swarm`. It is the operations intelligence layer.

**What `/swarm` does:** Execute. Read plan, validate, decompose, dispatch, merge, review, report.
**What the agent does:** Operate. Handle the unexpected, make judgment calls, adapt.

### Pre-launch intelligence

- Find plan files in the project: "I found `docs/plans/saas-plan.md`, last modified 2 hours ago. Use this one?"
- Check project readiness: "`project-context.md` exists but `project-contract.md` is missing. Run `/plan` first to generate it."
- Validate resource availability: "This plan has 6 features in Wave 1. I recommend max-concurrency of 3. Run 2 batches within Wave 1?"
- Handle ambiguity: "Swarm this but skip billing" → modifies execution plan, then runs
- Detect resume opportunities: "Previous swarm halted at Wave 3. Auth failed due to a missing env var. Want me to fix the setup and resume?"

### Runtime adaptation

- If an agent fails and the failure is a known pattern (missing dependency, wrong import path), update the learnings file and advise whether to retry or skip
- If a wave takes unexpectedly long, report status without being asked
- If merge conflicts are detected during the sequential merge queue, resolve them using contract conventions and workbranch intent
- If the halt condition triggers, explain why and offer options (rollback, retry failed feature, continue anyway)

### Post-run analysis

- "3 features failed. Auth failed due to a missing env var — that's a setup issue, not a code issue. Want me to fix `project-context.md` and retry just the auth workbranch?"
- "The integration reviewer found 12 issues but 10 are the same naming pattern. Want me to do a bulk rename?"
- "Wave 2 had contract deviations in 2 features. Here's what changed and why."

The agent is the thing you talk to after the swarm finishes. `/swarm` gives you a report. The agent gives you a conversation about what happened and what to do next.

Does NOT replicate `/plan` — if no plan exists, directs the user to run `/plan` or `/import-plan` first.

---

## Workbranch File Format

Generated by the decomposer agent. One file per workbranch, stored at `docs/workbranches/<plan-slug>/`.

```markdown
# Workbranch: <Name>

## Description
<Natural language description from the plan>

## Sub-features
1. <Sub-feature name> — <brief description>
2. <Sub-feature name> — <brief description>
3. ...

## Owns (predicted)
- <file or directory path this workbranch expects to create/modify>
- <file or directory path>
- ...

## Dependencies
<comma-separated workbranch names, or "none">

## Wave
<assigned wave number>

## Context
- Platform: <platform name>
- Plan: <path to plan file>
- Contract: docs/project-contract.md
- Learnings: docs/wave-learnings.md
- Base branch: <from project-context.md>
- Status: pending | in-progress | merged | failed | blocked
```

The sub-features list becomes the Implementation Order seed for the auto-dev agent's Phase 1. The agent uses it as a starting point — it may adjust ordering or split steps further based on codebase exploration, but it must implement all listed sub-features.

The `Owns (predicted)` section is finalized during the Phase 1 sync point based on the agent's actual architecture plan. Predicted ownership is used for initial conflict detection during decomposition.

---

## Integration Reviewer

Triggered after all waves complete. Its scope is reduced because the wave-transition agent has already handled most per-feature compliance.

Receives:
- The original plan document
- The project contract (final version, after all wave updates)
- The wave learnings file
- List of all merged PRs
- List of all failed/blocked features

### Checks
1. **Completeness** — every feature in the plan has corresponding code (or is explicitly failed/blocked)
2. **Cross-wave consistency** — features from different waves interact correctly
3. **Contract compliance** — remaining deviations not caught by wave-transition agent
4. **Duplication** — no utility functions, components, or patterns reimplemented across features
5. **Conventions** — all features follow the coding conventions from project-context.md
6. **Dead code** — no orphaned imports, unused exports, or placeholder code left behind

### Output
- Opens a cleanup PR with fixes for issues found
- Includes a summary in the PR body of what was fixed and what needs manual attention
- Flags any contract deviations — some may be legitimate (agent found a better approach), some may be bugs

---

## Final Report Format

Written to `docs/reports/swarm-<date>-report.md`:

```markdown
# Swarm Report — <Platform Name>

**Date:** <timestamp>
**Plan:** <path to plan file>
**Contract:** docs/project-contract.md
**Learnings:** docs/wave-learnings.md
**Duration:** <total wall-clock time>

## Summary
- Features planned: <N>
- Features merged: <N>
- Features failed: <N>
- Features blocked: <N>
- Waves executed: <N>
- Contract updates: <N>
- Integration PR: <URL or "none needed">
- Rollback tags: swarm/<slug>/pre-wave-1 through post-wave-<N>

## Wave Execution

### Wave 1
- **Features:** auth (merged), config (merged)
- **Merge order:** auth → config
- **Phase 1 sync:** no ownership conflicts
- **Wave transition:** 0 issues, 1 contract update, 4 learnings
- **Halt check:** 0% blocked → continue

### Wave 2
...

## Features

### <Feature Name>
- **Status:** merged | failed | blocked
- **Wave:** <N>
- **Sub-features:** <N completed> / <N planned>
- **PR:** <URL>
- **Review iterations:** <N>
- **Contract deviations:** <list or "none">
- **Notes:** <any issues, deviations from plan>

### <Feature Name>
...

## Integration Review
- Issues found: <N>
- Issues fixed: <N>
- Contract deviations found: <N>
- Issues needing manual attention: <N>
- Cleanup PR: <URL>

## Failures & Blocked Features

### <Feature Name> (FAILED)
- **Reason:** <build failure, review loop exhausted, merge conflict, etc.>
- **Last error:** <summary>
- **Rollback tag:** swarm/<slug>/pre-wave-<N>

### <Feature Name> (BLOCKED)
- **Blocked by:** <failed feature name>
```

---

## Components to Build

### New commands
1. `develop-plugin/commands/plan.md` — three-phase interactive plan + contract + conditional decomposition with approval gates
2. `develop-plugin/commands/import-plan.md` — parse external brainstorm → plan + contract with mandatory confirmation
3. `develop-plugin/commands/swarm.md` — orchestrator entry point with wave lifecycle, staleness detection, and partial re-runs

### New agents
4. `develop-plugin/agents/swarm-orchestrator.md` — ops layer: pre-launch intelligence, runtime adaptation, conflict resolution, post-run analysis
5. `develop-plugin/agents/decomposer.md` — feature → workbranch + sub-feature decomposition with predicted ownership; codebase-aware for existing projects
6. `develop-plugin/agents/wave-transition.md` — single-pass post-wave agent: micro-review + contract validation + knowledge extraction

### New skills
7. `develop-plugin/skills/integration-reviewer/SKILL.md` — final post-merge review against plan + contract + learnings

### New templates
8. `develop-plugin/skills/autonomous-feature-developer/assets/project-contract.template.md` — contract template

### Modifications to existing
9. `develop-plugin/commands/auto-dev.md` — accept workbranch file as input (in addition to free-text), read wave-learnings.md
10. `develop-plugin/skills/autonomous-feature-developer/SKILL.md` — read project contract in Phase 1, read wave-learnings.md in Wave 2+, use sub-features as implementation order seed, support Phase 1 sync point (report file list before proceeding to Phase 2)
11. `develop-plugin/commands/init.md` — optionally set up `docs/plans/`, `docs/workbranches/`, and `docs/reports/` directories

---

## Further R&D Questions

These are open research areas that need exploration before implementation:

### 1. Auto-dev agent prompting strategy
What exactly goes into the agent prompt to ensure it follows the contract without being too rigid? How do you balance "follow the contract for User model shape" with "adapt freely when the contract doesn't cover something"? What's the failure mode when contract instructions conflict with what the agent discovers in the codebase? Should the agent be told to flag deviations, silently adapt, or hard-fail?

### 2. Sub-feature scope explosion
What happens when a sub-feature turns out to be bigger than expected mid-implementation? Should the agent split it further autonomously, push through regardless, or signal back to the orchestrator? Is there a size heuristic (lines changed, number of files, time spent) that triggers a scope warning?

### 3. Agent resource limits
How many parallel agents can reasonably run? Context window limits, API rate limits, and machine resources (CPU/memory for builds) all constrain parallelism. Should there be a configurable max-concurrency? What's the queuing strategy when there are more workbranches in a wave than available agent slots?
