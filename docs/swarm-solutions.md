# Swarm Orchestrator — Solutions to Design Critique

**Date:** 2026-03-14
**Related:** [swarm-orchestrator-design.md](./swarm-orchestrator-design.md)

---

## 1. Contract fragility — Wave 1 as a proving ground

The contract is written before code exists. Wave 1 is the first time it meets reality.

**Solution: Post-wave contract validation step.**

After Wave 1 merges, the orchestrator runs a contract validator before starting Wave 2:

```
Wave 1 completes → all PRs merged
    │
    ▼
Contract validator agent:
  - Read the merged codebase
  - Diff actual file structure vs contract's File Structure section
  - Diff actual model shapes vs contract's Models section
  - Diff actual API patterns vs contract's API section
  - Produce a deviation report
    │
    ▼
Deviations found?
  - None → proceed to Wave 2
  - Minor (naming differences, extra fields) → auto-update contract, proceed
  - Major (wrong ORM, different auth pattern) → update contract, log warning, proceed
```

The contract becomes a living document that self-corrects after each wave. The key constraint: contract updates are additive/corrective only. You can add a field to a model or change a file path, but you can't remove a model that Wave 1 already implemented.

This means Wave 1 should include the most foundational features — auth, data models, core config — because they're the ones that test the contract most aggressively.

---

## 2. `/plan` overload — split into phases with separate approval gates

`/plan` currently does six things in one flow. Split it into three distinct phases with a user confirmation between each:

**Phase A — Feature planning:**
- Core questions (platform, stack, deployment)
- Free-form feature exploration
- Output: plan document draft
- **User confirms plan before proceeding**

**Phase B — Convention negotiation:**
- Ask about shared models, API style, auth, file structure, patterns
- Output: project contract draft
- **User confirms contract before proceeding**

**Phase C — Decomposition preview:**
- Break features into workbranches with sub-features
- Assign dependencies and waves
- Output: wave execution preview
- **User confirms decomposition before saving**

Each phase produces one artifact. The user approves each independently. A bad contract doesn't silently contaminate the decomposition because the user reviews them separately.

Implementation-wise, `/plan` is still one command — it just has three internal checkpoints. If the user says "the contract looks wrong," you fix it without redoing the feature planning.

---

## 3. Decomposer — define it as an agent with explicit heuristics

The decomposer isn't a parser — it's an LLM reasoning task. Define it as a dedicated agent with clear instructions:

**Decomposer agent prompt structure:**

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

**Workbranch boundary heuristics:**

The decomposer also decides workbranch boundaries (whether "User Authentication" stays as one workbranch or splits into two). The rule:

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

---

## 4. Cross-wave learning — shared knowledge file

After each wave merges, the orchestrator produces a learnings file that subsequent waves read.

**Mechanism:**

```
Wave 1 merges
    │
    ▼
Orchestrator runs a "knowledge extraction" agent:
  - Read the merged diffs from all Wave 1 PRs
  - Read any commit messages noting deviations from the plan
  - Extract practical discoveries:
    - Build quirks ("vite requires explicit .tsx extension in imports")
    - ORM behaviors ("prisma needs explicit @map for snake_case columns")
    - File structure realities ("src/lib/ is reserved for framework internals,
      use src/utils/ instead")
    - Dependency notes ("zod v3.23+ required for .pipe() transforms")
    │
    ▼
Write to: docs/wave-learnings.md (appended per wave)
```

**Format:**

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

Every auto-dev agent in Wave 2+ reads this file alongside the project context and contract. It's append-only — waves never edit previous waves' learnings.

---

## 5. Integration timing — per-wave micro-reviews

Replace the single end-of-pipeline integration review with incremental checks:

**After each wave merges:**

```
Wave N PRs all merged
    │
    ▼
Micro-review agent (lightweight, fast):
  1. Contract compliance check
     - Do merged files follow contract's file structure?
     - Do models match contract shapes?
  2. Conflict scan
     - Any duplicate utility functions across Wave N features?
     - Any conflicting exports or naming collisions?
  3. Base branch health check
     - Does the build pass on the base branch after all merges?
     - Any broken imports from merge ordering?
    │
    ▼
Issues found?
  - None → proceed to Wave N+1
  - Minor → auto-fix, commit to base branch, proceed
  - Major → fix, update contract/learnings, proceed
```

**The full integration reviewer still runs at the end**, but its job is smaller — it handles cross-wave concerns and completeness checking that micro-reviews can't catch. Most of the per-feature compliance issues are already resolved.

Pipeline becomes:

```
Wave 1 → merge → micro-review → contract update → learnings
Wave 2 → merge → micro-review → contract update → learnings
Wave 3 → merge → micro-review → contract update → learnings
Final integration review (completeness + cross-wave concerns)
```

---

## 6. `/import-plan` — always draft, always confirm

Remove the ambiguity. `/import-plan` follows a strict protocol:

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
9. Save both files
```

**Never silently write conventions.** The contract is too important for inference without confirmation. The plan can tolerate minor inference errors (the user will catch them in the preview), but the contract must be explicitly approved.

---

## 7. Rollback strategy — wave tags + revert plan

Each wave creates a git tag before and after merging. This gives clean rollback points.

**Mechanism:**

```bash
# Before Wave 1 starts
git tag swarm/<slug>/pre-wave-1

# After Wave 1 merges
git tag swarm/<slug>/post-wave-1

# Before Wave 2 starts
git tag swarm/<slug>/pre-wave-2

# ... and so on
```

**If something goes catastrophically wrong in Wave N:**

The orchestrator can:
1. Stop all in-flight agents
2. Revert to `swarm/<slug>/post-wave-(N-1)` — the last known good state
3. Report what happened and which wave failed

**Revert command (for the user):**

```bash
git revert --no-commit swarm/<slug>/post-wave-(N-1)..HEAD
git commit -m "revert: roll back to post-wave-(N-1)"
```

This doesn't use `git reset --hard` (which is in the deny list) — it creates a new revert commit that undoes the changes. Safe and auditable.

Add to the orchestrator: if a wave produces more failures than successes, halt the swarm and suggest a rollback rather than continuing into broken territory.

---

## 8. Same-wave merge conflicts — sequential merge with rebase

When multiple PRs in the same wave are ready to merge, don't merge them simultaneously. Use a sequential merge queue:

**Mechanism:**

```
Wave 1 agents finish: [auth PR, config PR, logging PR]
    │
    ▼
Merge queue (sequential):
  1. Merge auth PR (squash)
  2. Rebase config PR onto updated base → merge (squash)
  3. Rebase logging PR onto updated base → merge (squash)
```

Each PR is rebased onto the latest base before merging. If the rebase has conflicts, the orchestrator runs a conflict resolution agent:

```
Conflict resolution agent:
  - Read the conflicting files
  - Read both PRs' intent from their workbranch files
  - Resolve conflicts favoring the contract's conventions
  - If unresolvable automatically, mark the PR as failed
    (don't produce bad merges)
```

**Merge ordering within a wave:**

Priority determines merge order within a wave (higher priority merges first). This means high-priority features' code is the "ground truth" that lower-priority features rebase onto. This naturally gives foundational features precedence.

**File ownership scoping (preventive):**

Add an optional `Owns` field to workbranch files:

```markdown
## Owns
- src/models/user.ts
- src/routes/auth/*.ts
- src/middleware/auth.ts
```

The decomposer assigns ownership based on sub-features. If two workbranches in the same wave claim the same file, the decomposer flags it during decomposition and either reassigns or moves one workbranch to a later wave.

---

## 9. Swarm-orchestrator agent — define as the "ops layer"

Give the agent a clear, differentiated role. It's not just a conversational wrapper — it's the operations intelligence layer.

**What `/swarm` does:** Execute. Read plan, validate, decompose, dispatch, merge, review, report.

**What the agent does:** Operate. Handle the unexpected, make judgment calls, adapt.

Specific capabilities the agent has that `/swarm` does not:

### Pre-launch intelligence
- Find plan files in the project: "I found docs/plans/saas-plan.md, last modified 2 hours ago. Use this one?"
- Check project readiness: "project-context.md exists but project-contract.md is missing. Run /plan first to generate it."
- Validate resource availability: "This plan has 6 features in Wave 1. I recommend max-concurrency of 3. Run 2 batches within Wave 1?"

### Runtime adaptation
- If an agent fails and the failure is a known pattern (missing dependency, wrong import path), update the learnings file and advise whether to retry or skip
- If a wave takes unexpectedly long, report status without being asked
- If merge conflicts are detected, decide whether to auto-resolve or escalate

### Post-run analysis
- "3 features failed. Auth failed due to a missing env var — that's a setup issue, not a code issue. Want me to fix project-context.md and retry just the auth workbranch?"
- "The integration reviewer found 12 issues but 10 are the same naming pattern. Want me to do a bulk rename?"

The agent is the thing you'd talk to after the swarm finishes. `/swarm` gives you a report. The agent gives you a conversation about what happened and what to do next.
