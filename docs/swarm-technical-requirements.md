# Swarm Orchestrator — Technical Requirements

**Status:** Implementation-ready
**Date:** 2026-03-14
**Source:** Translates `swarm-orchestrator-design.md` into concrete implementation specs
**Target directory:** `develop-plugin/` (relative to repository root)

This document is the single authoritative reference for implementing the swarm orchestrator update. It does not re-explain rationale — consult the design document for that. Every section here is a build spec. An implementer should be able to complete the entire update using only this document.

---

## Table of Contents

1. Plugin Structure — Final Directory Tree
2. plugin.json Updates
3. New Command: /plan
4. New Command: /import-plan
5. New Command: /swarm
6. New Agent: swarm-orchestrator
7. New Agent: decomposer
8. New Agent: wave-transition
9. New Skill: integration-reviewer
10. Modified Command: /auto-dev
11. Modified Skill: autonomous-feature-developer/SKILL.md
12. Modified Reference: phase-1-architecture.md
13. Modified Command: /init
14. Scripts — New and Modified
15. Templates
16. Swarm State Schema and File Lifecycle
17. Wave Execution Engine — Agent Dispatch Contracts
18. Phase 1 Sync Point Mechanism
19. Sequential Merge Queue
20. Wave-Transition Agent Invocation Contract
21. File Formats Reference
22. Cross-Cutting Concerns

---

## 1. Plugin Structure — Final Directory Tree

New paths are marked `[NEW]`. Modified paths are marked `[MOD]`. Unchanged paths are unmarked. No existing file is deleted.

```
develop-plugin/
├── .claude-plugin/
│   └── plugin.json                                                  [MOD]
│
├── commands/
│   ├── auto-dev.md                                                   [MOD]
│   ├── init.md                                                       [MOD]
│   ├── plan.md                                                       [NEW]
│   ├── import-plan.md                                                [NEW]
│   └── swarm.md                                                      [NEW]
│
├── agents/
│   ├── swarm-orchestrator.md                                         [NEW]
│   ├── decomposer.md                                                 [NEW]
│   └── wave-transition.md                                            [NEW]
│
└── skills/
    ├── autonomous-feature-developer/
    │   ├── SKILL.md                                                  [MOD]
    │   ├── assets/
    │   │   ├── project-context.template.md
    │   │   └── project-contract.template.md                         [NEW]
    │   ├── references/
    │   │   ├── phase-1-architecture.md                              [MOD]
    │   │   ├── phase-2-implementation.md
    │   │   ├── phase-3-pull-request.md
    │   │   ├── phase-4-review-fix.md
    │   │   └── review-rubric.md
    │   └── scripts/
    │       ├── setup.sh                                             [MOD]
    │       ├── verify.sh
    │       ├── create-pr.sh
    │       ├── merge-cleanup.sh
    │       └── swarm-rebase-merge.sh                                [NEW]
    │
    └── integration-reviewer/
        └── SKILL.md                                                  [NEW]
```

The `agents/` directory is new. Create it at `develop-plugin/agents/`.

---

## 2. plugin.json Updates

**File:** `develop-plugin/.claude-plugin/plugin.json`

**Change:** Version bump from `1.0.0` to `2.0.0`. Add `commands`, `agents`, and `skills` registry arrays. These are informational — they let tooling enumerate available components.

**Final file content:**

```json
{
  "name": "develop-plugin",
  "version": "2.0.0",
  "description": "Autonomous feature developer and swarm orchestrator — builds features from request to merged PR, and orchestrates parallel agent swarms for full-platform development.",
  "author": {
    "name": "Vierkandt"
  },
  "repository": "https://github.com/Vierkandt/claude-autonomous-feature-dev",
  "commands": [
    "commands/init.md",
    "commands/auto-dev.md",
    "commands/plan.md",
    "commands/import-plan.md",
    "commands/swarm.md"
  ],
  "agents": [
    "agents/swarm-orchestrator.md",
    "agents/decomposer.md",
    "agents/wave-transition.md"
  ],
  "skills": [
    "skills/autonomous-feature-developer/SKILL.md",
    "skills/integration-reviewer/SKILL.md"
  ]
}
```

---

## 3. New Command: /plan

**File:** `develop-plugin/commands/plan.md`

### YAML frontmatter

```yaml
---
name: plan
description: "Interactively brainstorm and structure a software platform plan. Runs three phases with approval gates: (A) feature planning with guided questions, (B) convention negotiation producing a project contract, (C) conditional decomposition preview for new projects. Produces docs/plans/<slug>-plan.md, docs/project-contract.md, and optionally docs/workbranches/<slug>/. Run before /swarm."
argument-hint: "[optional: project name or starting topic]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---
```

### Instruction body

The command body must implement the following protocol. Structure it with explicit numbered steps matching the phases below.

**Step 1 — Determine starting point**

If `$ARGUMENTS` is non-empty, use it as the opening context. Otherwise begin cold.

**Step 2 — Phase A: Feature planning**

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

Produce a plan document draft using the format in section 21. Display it inline.

Gate: Display the plan and ask: "Here's the structured plan. Does this look right? Say 'yes' to continue to conventions, or tell me what to change." Do not proceed to Phase B until the user explicitly confirms.

**Step 3 — Phase B: Convention negotiation**

After Phase A is confirmed, transition: "Now let's define the shared conventions every agent will follow. These become hard constraints — every auto-dev agent in the swarm will follow them exactly."

Ask about each contract section in sequence. For each, propose a sensible default based on the stack confirmed in Phase A:

- "What does the user model look like? List fields and types." (Or: "Based on your stack, here's a starting User model — does this look right?")
- "REST or GraphQL? What's the base URL pattern? How are errors shaped?"
- "How does auth work? JWT, session cookies, OAuth? Where does the middleware live?"
- "Where do routes, models, middleware, and utilities live in the file structure?"
- "Any shared patterns? Repository pattern, validation library, auth guard wrapper?"

After collecting answers, produce a project contract draft using the format in section 21. Display it inline.

Gate: "Here's the project contract. Review it carefully — every agent in the swarm follows it exactly. Say 'yes' to continue, or correct anything that's wrong." Do not proceed to Phase C until the user explicitly confirms. If the user corrects anything, update the contract and re-display it without re-running Phase A.

**Step 4 — Phase C: Decomposition preview (conditional)**

Check whether a source directory exists:

```bash
ls -d src app lib 2>/dev/null | head -1
```

If a source directory exists (existing project): Skip Phase C. Tell the user: "This looks like an existing project. Decomposition will happen when you run `/swarm` — the decomposer needs to explore your codebase first to avoid conflicts with existing code. Saving plan and contract now." Jump to Step 5.

If no source directory exists (new project): Invoke the `decomposer` agent via the Agent tool. Provide the plan content, contract content, plan slug, and `is_existing_project: false`.

After the decomposer completes (it will have written workbranch files), display a wave execution preview:

```
Wave execution plan:

Wave 1 (parallel): <workbranch names>
Wave 2 (parallel): <workbranch names>
...

Merge order within each wave: <priority order>
Total: N workbranches across N waves.
```

Gate: "Here's how the work will be decomposed. Say 'yes' to save everything, or tell me what to adjust." If the user wants changes, re-run the decomposer with the correction. If the user says the contract is wrong, return to Phase B without re-running Phase A. Each phase is independently revisable.

**Step 5 — Save outputs**

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

### Input/output contract

- Input: optional `$ARGUMENTS` (starting topic string)
- Output files written: `docs/plans/<slug>-plan.md`, `docs/project-contract.md`, optionally `docs/workbranches/<slug>/*.md`
- No git operations, no builds, no PRs

### Dependencies

- Invokes the `decomposer` agent (via Agent tool) during Phase C for new projects only
- May read `docs/project-context.md` if it exists, to orient on existing stack details

### Allowed tools

`Read, Write, Edit, Glob, Grep, Bash, Agent`

---

## 4. New Command: /import-plan

**File:** `develop-plugin/commands/import-plan.md`

### YAML frontmatter

```yaml
---
name: import-plan
description: "Parse a brainstorm document (exported from Claude.ai or any source) into a structured plan and project contract. Accepts a file path or inline pasted text as the argument. Always presents drafts for confirmation before writing — never silently infers conventions. Usage: /import-plan <file-path>  OR  /import-plan <pasted brainstorm text>"
argument-hint: "<file-path or pasted brainstorm text>"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---
```

### Instruction body

**Step 1 — Resolve input**

If `$ARGUMENTS` is empty: ask "Please paste your brainstorm text or provide a file path."

If `$ARGUMENTS` looks like a file path (contains `/` or `.md` extension): check whether it exists with `[ -f "$ARGUMENTS" ]`. If yes, read it. If no, treat `$ARGUMENTS` as inline text.

Otherwise treat `$ARGUMENTS` as the raw brainstorm text.

**Step 2 — Extract features**

Parse the input text using best-effort inference. Look for:
- Numbered lists, bullet points, or headings that describe features
- Phrases like "users can...", "the system should...", "we need..."
- Dependency hints: "requires X", "needs X to be done first", "after X", "depends on X"
- Priority hints: "core feature", "critical", "must have", "nice to have", "later", "v2"
- Stack information: framework names, database names, hosting names

Build a structured feature list from everything found.

**Step 3 — Present plan draft**

Display the extracted plan in the canonical format from section 21. Lead with: "I found N features. Here's the structured plan:"

Gate: "Does this look right? Any features missing, misnamed, or with wrong dependencies?" Wait for explicit confirmation. Accept corrections and re-display. Do not proceed until the user says "yes" or equivalent affirmation.

**Step 4 — Infer conventions**

From the brainstorm text, identify any mentioned conventions: specific model names and fields, API patterns, framework choices, file structure mentions.

**Step 5 — Present contract draft**

Display the inferred contract draft in canonical format from section 21. Lead with: "Based on the brainstorm, here's a draft project contract:"

Prominently warn: "Review this carefully. Every auto-dev agent in the swarm will follow it exactly. Do not approve a contract that contains guesses you have not verified."

Gate: Wait for explicit user confirmation or corrections. Apply corrections, re-display. Do not proceed until explicitly approved. If the user approves technical details with only a vague "looks good," ask them to specifically confirm the model fields and API patterns before continuing.

**Step 6 — Decomposition preview (conditional)**

Same logic as `/plan` Step 4: check for existing source directory. New project: invoke decomposer, show preview with gate. Existing project: skip, inform user.

**Step 7 — Save outputs**

Same as `/plan` Step 5: derive slug, `mkdir -p`, write plan, write contract (with backup if existing), confirm paths.

### Input/output contract

- Input: `$ARGUMENTS` — file path or raw brainstorm text (required, but ask if empty)
- Output files written: `docs/plans/<slug>-plan.md`, `docs/project-contract.md`, optionally `docs/workbranches/<slug>/*.md`
- No git operations, no builds, no PRs

### Dependencies

- Invokes `decomposer` agent during Step 6 for new projects

### Allowed tools

`Read, Write, Edit, Glob, Grep, Bash, Agent`

---

## 5. New Command: /swarm

**File:** `develop-plugin/commands/swarm.md`

### YAML frontmatter

```yaml
---
name: swarm
description: "Execute a swarm of parallel auto-dev agents against a plan file. Dispatches one agent per workbranch, manages wave ordering and dependency sequencing, handles the sequential merge queue, runs post-wave reviews, and produces a final report. Usage: /swarm <plan-file-path>. Requires docs/project-context.md and docs/project-contract.md. Run /plan or /import-plan first."
argument-hint: "<path to plan file, e.g. docs/plans/my-platform-plan.md>"
user-invocable: true
context: fork
agent: general-purpose
allowed-tools: Edit, Write, Glob, Grep, Read, Bash, Agent
---
```

### Instruction body

**Step 1 — Verify environment**

```bash
echo "AGENT_TEAMS=${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-NOT_SET}"
```

If the output is `AGENT_TEAMS=NOT_SET`, stop immediately and display this message:

```
/swarm requires agent teams and elevated permissions.

Add the following to your .claude/settings.local.json and restart Claude Code:

{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "permissions": {
    "allow": [
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "Read",
      "NotebookEdit",
      "Bash(*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git reset --hard*)",
      "Bash(git push --force*)",
      "Bash(git clean *)"
    ]
  }
}

Then re-run: /swarm <plan-file-path>
```

If the output is `AGENT_TEAMS=1`, proceed to Step 2.

**Step 2 — Resolve plan file**

`PLAN_FILE="$ARGUMENTS"`. If empty, stop with: "Usage: /swarm <path-to-plan-file>. Run /plan or /import-plan first to generate a plan."

Verify the file exists:

```bash
[ -f "$PLAN_FILE" ] || { echo "ERROR: plan file not found: $PLAN_FILE"; exit 1; }
```

Derive `PLAN_SLUG`:

```bash
PLAN_SLUG=$(basename "$PLAN_FILE" | sed 's/-plan\.md$//' \
  | tr '[:upper:]' '[:lower:]' \
  | sed 's/[^a-z0-9]/-/g' \
  | sed 's/-\+/-/g' \
  | sed 's/^-//;s/-$//' \
  | cut -c1-50)
```

**Step 3 — Check for existing swarm state**

```bash
STATE_FILE="docs/workbranches/${PLAN_SLUG}/swarm-state.json"
```

If `$STATE_FILE` exists, read it. Extract `status` and `current_wave`.

If `status` is `"halted"` or `"in-progress"`, ask:

```
Previous swarm for this plan halted at Wave <current_wave>.
Resume from Wave <current_wave>, or start fresh? (resume/fresh)
```

- If "fresh": delete `$STATE_FILE`. Proceed to Step 4.
- If "resume": load `failed_features`, `blocked_features`, `wave_results`, `waves_completed`, `tags` from the state file. Set `RESUMING=true`. Jump to Step 9 (wave loop) starting at `current_wave`. Skip Steps 4–8.

If the state file does not exist, proceed normally.

**Step 4 — Validate plan**

Read `$PLAN_FILE`. Parse all features by scanning for `### Feature:` headings and extracting the Name, Dependencies, and Priority label lines that follow each heading.

Validations (stop on any failure, listing all errors found):
1. All feature names are unique (case-insensitive comparison)
2. All dependency references name features that exist in the plan (case-sensitive match against feature names)
3. No circular dependencies — perform topological sort; if it fails, report the cycle: "Circular dependency detected: FeatureA → FeatureB → FeatureA"

**Step 5 — Validate contract**

```bash
[ -f "docs/project-contract.md" ] || {
  echo "ERROR: docs/project-contract.md is missing."
  echo "Run /plan or /import-plan to generate it."
  exit 1
}
```

Read the contract. Run internal consistency checks (stop on failure, list all issues):
- Every model name referenced in the API or Patterns sections must be defined in the Models section
- No path in File Structure contradicts a path in Patterns
- No section references a concept defined nowhere else in the contract

These checks are heuristic. If a check is ambiguous, log a warning and continue rather than stopping.

**Step 6 — Validate project context**

```bash
[ -f "docs/project-context.md" ] || {
  echo "ERROR: docs/project-context.md is missing. Run /init first."
  exit 1
}
```

Read the context file. Extract and store:
- `BASE_BRANCH` (default: `main`)
- `MERGE_STRATEGY` (default: `--squash`)
- `PR_CLI` (default: `gh`)
- `BUILD_CMD` (required — stop if empty: "ERROR: build command not found in docs/project-context.md")
- `TEST_CMD` (optional, default empty)
- `LINT_CMD` (optional, default empty)

**Step 7 — Staleness check and decomposition**

```bash
WB_DIR="docs/workbranches/${PLAN_SLUG}"
WB_COUNT=$(find "$WB_DIR" -name "*.md" -not -name "swarm-state.json" 2>/dev/null | wc -l)
```

If `WB_COUNT > 0`, compare modification times:

```bash
# Portable mtime: try Linux stat first, fall back to macOS stat
get_mtime() {
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null
}
PLAN_MTIME=$(get_mtime "$PLAN_FILE")
WB_MTIME=$(find "$WB_DIR" -name "*.md" -not -name "swarm-state.json" \
  | while read -r f; do get_mtime "$f"; done | sort -n | tail -1)
```

If `PLAN_MTIME > WB_MTIME`: print "Plan was modified since last decomposition. Re-decomposing." Then invoke the decomposer agent (prompt in section 17).

If `WB_COUNT == 0`: invoke the decomposer agent.

If `WB_COUNT > 0` and plan is not newer: use existing workbranch files.

After decomposition (or using existing files), read all `*.md` files from `$WB_DIR` (excluding `swarm-state.json`) to build the workbranch list.

**Step 8 — Build dependency graph and print execution plan**

Read all workbranch files. For each file, extract: the `# Workbranch: <Name>` heading, `## Dependencies` section, `## Priority` section, and `## Wave` section.

If Wave fields are missing, compute wave assignment via topological sort:
- Workbranches with `Dependencies: none` → Wave 1
- Workbranches whose all dependencies are assigned to wave N or earlier → Wave N+1

Sort workbranches within each wave by priority (high → medium → low → alphabetical tiebreak).

Print:

```
Swarm execution plan — <Platform Name>

Wave 1 (2 workbranches, parallel):
  1. auth (high)
  2. config (medium)
  Merge order: auth → config

Wave 2 (2 workbranches, parallel):
  1. dashboard (high) — depends on: auth
  2. billing (medium) — depends on: config
  Merge order: dashboard → billing

Total: 4 workbranches across 2 waves.
```

**Step 9 — Initialize swarm state**

If not resuming:

```bash
mkdir -p "docs/workbranches/${PLAN_SLUG}"
```

Write `docs/workbranches/${PLAN_SLUG}/swarm-state.json` with initial state (schema in section 16).

**Step 10 — Wave execution loop**

For each wave N in order (starting from `current_wave` on resume):

**10a.** If `N` is in `waves_completed`, skip to the next wave.

**10b. Tag pre-wave:**

```bash
git tag "swarm/${PLAN_SLUG}/pre-wave-${N}"
git push origin "swarm/${PLAN_SLUG}/pre-wave-${N}"
```

Append the tag to the state file's `tags` array. Write the updated state file.

**10c. Collect workbranches for this wave.** Read all workbranch files whose `## Wave` section equals N. Exclude any whose slug is in `failed_features` or `blocked_features`.

**10d. Dispatch auto-dev agents (parallel).** For each workbranch in the wave's set, invoke one Agent tool call (prompt template in section 17). All agents are dispatched concurrently — do not wait for agent N to finish before dispatching agent N+1.

**10e. Phase 1 sync point.** See section 18 for the full protocol. The orchestrator polls for `<workbranch-slug>-phase1-report.json` files, resolves conflicts, and writes `<workbranch-slug>-phase1-resolution.json` files.

**10f. Wait for all agents to finish Phase 2–5.** Poll every 60 seconds for `<workbranch-slug>-done.json` files in `docs/workbranches/${PLAN_SLUG}/`. If an agent has produced no done marker for more than 60 minutes, mark it as failed with reason "agent timeout (60 min)."

**10g. Sequential merge queue.** See section 19 for the full algorithm.

**10h. Tag post-wave:**

```bash
git tag "swarm/${PLAN_SLUG}/post-wave-${N}"
git push origin "swarm/${PLAN_SLUG}/post-wave-${N}"
```

Append the tag to the state file's `tags` array.

**10i. Run wave-transition agent.** See section 20 for the invocation prompt. Wait for the agent to complete. Parse the `WAVE_TRANSITION_COMPLETE` block from its output.

**10j. Update swarm state.** Add N to `waves_completed`. Set `wave_results[N]` to a map of each workbranch slug → its status (from its done marker or merge queue result). Increment `current_wave` to N+1. Refresh `updated_at`. Write the state file.

**10k. Halt check.**

Compute:
- `total_remaining` = count of workbranches not in any `waves_completed` wave's results
- `now_blocked` = count of workbranches transitively blocked by failures from this wave that were not already in `blocked_features`

Add `now_blocked` workbranch slugs to `blocked_features` in the state file.

Special case: if ALL workbranches in wave N failed, halt immediately without computing the percentage.

Otherwise: if `len(blocked_features) > 0.5 * total_remaining`, halt:

```
HALT: Wave N failures now block X of Y remaining features (Z%).

Failed this wave:       <list>
Transitively blocked:   <list>

To roll back to before Wave N:
  git revert --no-commit swarm/<PLAN_SLUG>/pre-wave-<N>..HEAD
  git commit -m "revert: roll back to pre-wave-<N>"

To resume after fixing the root cause:
  /swarm <PLAN_FILE>
  (answer "resume" at the prompt)
```

Update state: `status: "halted"`, `halt_reason: "..."`. Write state file. Stop execution.

Otherwise: log any failures and newly blocked features as warnings and continue to wave N+1.

**Step 11 — Final integration review**

After all waves complete, invoke the `integration-reviewer` skill via Agent tool (prompt in section 17). Wait for it to complete. Extract `INTEGRATION_REVIEW_PR_URL=<url>` from its output.

Update state: set `integration_pr_url` to the extracted value.

**Step 12 — Write final report**

Compose the report in the format from section 21. Determine the output path:

```bash
REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="docs/reports/swarm-${REPORT_DATE}-report.md"
# If file exists, add time suffix to avoid collision
[ -f "$REPORT_FILE" ] && REPORT_FILE="docs/reports/swarm-${REPORT_DATE}-$(date +%H-%M)-report.md"
```

Write the report. Then commit it along with the final state:

```bash
git add -- "$REPORT_FILE" "docs/workbranches/${PLAN_SLUG}/swarm-state.json"
git commit -m "docs: add swarm report $(date +%Y-%m-%d)"
```

Update state: `status: "completed"`, `report_path: "$REPORT_FILE"`. Write state file.

**Step 13 — Print terminal summary**

```
Swarm complete — <Platform Name>

  Features planned:   N
  Features merged:    N
  Features failed:    N
  Features blocked:   N
  Waves executed:     N
  Contract updates:   N
  Integration PR:     <URL or "none needed">
  Full report:        <REPORT_FILE>
```

### Input/output contract

- Input: `$ARGUMENTS` — path to plan file (required)
- Reads: plan file, `docs/project-context.md`, `docs/project-contract.md`
- Writes: `docs/workbranches/${PLAN_SLUG}/swarm-state.json`, `docs/project-contract.md` (via wave-transition agent), `docs/wave-learnings.md` (via wave-transition agent), `docs/reports/*.md`
- Git side effects: creates and pushes git tags, creates and merges PRs (via auto-dev agents), commits report and state file

### Allowed tools

`Edit, Write, Glob, Grep, Read, Bash, Agent`

---

## 6. New Agent: swarm-orchestrator

**File:** `develop-plugin/agents/swarm-orchestrator.md`

### YAML frontmatter

```yaml
---
name: swarm-orchestrator
description: "The swarm operations intelligence layer. Use when the user wants to launch, analyze, diagnose, or resume a swarm run in natural language. Handles pre-launch checks (find plan files, validate readiness, advise on concurrency), runtime adaptation (failure diagnosis, conflict resolution advice), and post-run analysis (explain failures, offer bulk fixes, suggest retries). Does NOT generate plans — directs users to /plan or /import-plan if no plan exists. Trigger on: 'swarm this', 'build the whole platform', 'orchestrate this', 'run the swarm', or when a user describes a multi-feature build and wants autonomous execution with guidance."
allowed-tools: Edit, Write, Glob, Grep, Read, Bash, Agent
---
```

Agents do not use `user-invocable`, `context`, or `argument-hint` fields.

### Instruction body

**Identity and scope**

You are the swarm operations layer. You handle the unexpected, make judgment calls, and adapt to runtime conditions. You are NOT a plan generator. If no plan exists, direct the user to `/plan` or `/import-plan` first and stop.

**Pre-launch intelligence**

When asked to launch a swarm or help with swarm setup, work through these checks before dispatching anything:

1. **Find plan files:**

```bash
find docs/plans -name "*-plan.md" 2>/dev/null | sort
```

Display found files with modification times. Ask which to use if more than one is found.

2. **Check project readiness:**
   - `docs/project-context.md` exists? If not: "Missing `docs/project-context.md`. Run `/init` first."
   - `docs/project-contract.md` exists? If not: "Missing `docs/project-contract.md`. Run `/plan` or `/import-plan` first."
   - Both exist? Read the contract and validate internal consistency (same heuristic checks as `/swarm` Step 5). Report any inconsistencies.

3. **Concurrency advisory:** Count Wave 1 workbranches from the workbranch files (or estimate from the plan). If > 4: "This plan has N workbranches in Wave 1. Running all in parallel is fine but may strain API rate limits. Proceed with all N, or would you like to batch them?"

4. **Resume detection:** If `swarm-state.json` exists and `status` is `"halted"`:
   - Read the state. Identify `halt_reason` and which features failed.
   - Look up each failed feature's done marker for the error summary.
   - Report: "The previous swarm halted because `<halt_reason>`. The root cause for `<feature>` appears to be `<error_summary>`. Options: (1) fix the issue and resume, (2) skip `<feature>` and its dependents and resume, (3) start fresh."

5. **Natural language modification:** Handle requests like "swarm this but skip billing" — read the workbranch files, confirm which workbranches to skip, update their `Status:` field to `blocked` in their workbranch files, then proceed.

**Runtime adaptation**

When invoked during a running swarm:
- Read `swarm-state.json` and report current wave, elapsed time (from `started_at`), completed/in-progress/failed counts.
- For reported failures, read the done marker and classify: setup issue (missing env var, missing dependency install) vs code issue (build failure) vs merge issue. For setup issues, offer to fix `docs/project-context.md` and retry the failed workbranch.
- For halt conditions, explain the dependency chain that led to halt. Provide the exact rollback command.

**Post-run analysis**

After a swarm completes or halts:
- Read the final report.
- Group failures by type. Surface patterns (e.g., "3 of 4 failures share the same missing import path").
- For integration reviewer findings, offer bulk operations: "10 of 12 issues are the same naming inconsistency. Want me to fix all at once?"
- For contract deviations found in the report, explain which are likely intentional improvements vs likely bugs.

**Hard constraint**

This agent does not invoke `/plan` or generate plans. If no plan exists: "I don't see a plan file in `docs/plans/`. Run `/plan` to create one interactively, or `/import-plan` to convert a brainstorm document."

### Allowed tools

`Edit, Write, Glob, Grep, Read, Bash, Agent`

---

## 7. New Agent: decomposer

**File:** `develop-plugin/agents/decomposer.md`

### YAML frontmatter

```yaml
---
name: decomposer
description: "Feature decomposer. Breaks a plan document's features into workbranch files with ordered sub-features, predicted file ownership, wave assignments, and dependency mappings. Codebase-aware for existing projects: explores the codebase before decomposing to avoid conflicts with existing code. Called by /plan (Phase C, new projects only) and /swarm. Not user-invocable."
allowed-tools: Read, Write, Glob, Grep, Bash
---
```

### Instruction body

**Identity**

You are a feature decomposer. Your job is to take a plan document and produce workbranch files. You reason about feature boundaries, sub-feature ordering, file ownership, and wave assignment. You do NOT make architecture decisions — that is the auto-dev agent's job.

**Input**

The caller provides:
- Plan document content (or path to read)
- Project contract content (or path to read)
- Project context content (or path to read)
- Plan slug (for output directory naming)
- `IS_EXISTING_PROJECT` flag (`"true"` or `"false"`)

**Codebase exploration (existing projects only)**

If `IS_EXISTING_PROJECT` is `"true"`, explore before decomposing:

```bash
find . -type d \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/.next/*' \
  -not -path '*/dist/*' \
  | sort | head -80
```

Also read: the primary entry point file, one example of an existing model/schema file, one example of an existing route/controller file, and the package.json or equivalent manifest.

Note what already exists. Sub-features must not re-implement existing functionality — they must integrate with it.

**Workbranch boundary decision**

For each feature in the plan, decide: one workbranch or split into multiple?

Split when:
- Would produce more than ~8 sub-features
- Has sub-features that could independently merge (e.g., API backend vs frontend UI)
- Spans two distinct layers that other features depend on independently

Do NOT split when:
- Sub-features are tightly coupled (one requires the other to already be in place)
- Feature already has 3–4 sub-features
- Splitting would create circular dependencies

If splitting: create two workbranch files with adjusted names (e.g., `auth-backend.md` and `auth-ui.md`). Add the backend as a dependency of the UI to preserve ordering.

**Sub-feature decomposition**

For each workbranch, produce an ordered sub-features list:

1. Each sub-feature touches 1–5 files and produces one logical commit
2. Order by dependency — foundations first
3. If the feature uses persistent data, the first sub-feature is always the data model/schema/migration
4. The last sub-feature is always integration/wiring (connecting the pieces to the rest of the app)
5. Each sub-feature description answers: "what files will this touch and what will they do?"

Do NOT:
- Create sub-features smaller than one file change
- Create standalone "write tests" sub-features — tests are included within each sub-feature
- Specify architecture decisions (which library, which design pattern) — that is the auto-dev agent's job

**File ownership assignment**

For each workbranch, produce an `Owns (predicted)` list:
- Use the contract's File Structure section as the primary source for path patterns
- Assign each anticipated file or directory to exactly one workbranch
- If two workbranches need the same file:
  - Option A: Reassign the file to the workbranch with the stronger claim. Note the reassignment.
  - Option B: Move one workbranch to a later wave to sequence the writes.
  - Never leave a conflict unresolved in the output.
- For existing projects, exclude files that already exist and will not be modified.

**Wave assignment**

1. Build the dependency graph from the workbranch Dependencies fields.
2. Topological sort: workbranches with `Dependencies: none` → Wave 1. Any workbranch whose all dependencies are in waves ≤ N → Wave N+1.
3. Write the computed wave number to each workbranch file's `## Wave` section.

**Output**

Create `docs/workbranches/<plan-slug>/` if it does not exist. Write one file per workbranch using the workbranch file format from section 21. File names: `<workbranch-name-slug>.md`.

Print a summary:

```
Decomposition complete.
Wave 1 (parallel): auth, config
Wave 2 (parallel): dashboard, billing
Wave 3: analytics
Total: 5 workbranches across 3 waves.
Ownership reassignments: 1
  - src/types/index.ts: reassigned from dashboard to auth (auth defines the base User type)
```

### Input/output contract

- Input: plan, contract, context content (or paths), plan slug, is-existing-project flag
- Output files: `docs/workbranches/<slug>/<workbranch-slug>.md` (one per workbranch)
- No git operations, no PRs, no builds

### Allowed tools

`Read, Write, Glob, Grep, Bash`

---

## 8. New Agent: wave-transition

**File:** `develop-plugin/agents/wave-transition.md`

### YAML frontmatter

```yaml
---
name: wave-transition
description: "Single-pass post-wave agent. Runs once after all PRs in a wave are merged. Reads the merged diffs once and produces three outputs in a single pass: (1) micro-review with auto-fixes for minor issues, (2) additive/corrective contract updates, (3) wave learnings appended to docs/wave-learnings.md. Called by /swarm. Not user-invocable."
allowed-tools: Edit, Write, Read, Glob, Grep, Bash
---
```

### Instruction body

**Identity**

You are the wave-transition agent. You run exactly once after a wave's PRs are all merged. You read the merged code once and produce three outputs. You do not spawn sub-agents. You do not fix architectural problems — only minor code issues such as a file in the wrong directory, an extra model field not yet in the contract, or a naming inconsistency.

**Input**

The caller provides in the invocation prompt:
- Wave number N
- Plan slug
- List of workbranch slugs that merged this wave
- List of workbranch slugs that failed this wave
- Pre-wave tag: `swarm/<plan-slug>/pre-wave-N`
- Post-wave tag: `swarm/<plan-slug>/post-wave-N`
- Paths: `docs/project-contract.md`, `docs/wave-learnings.md`
- Build, test, and lint commands
- Base branch and PR CLI

**Single-pass exploration**

Read the diffs for this wave once:

```bash
git diff swarm/<slug>/pre-wave-<N>..swarm/<slug>/post-wave-<N> --name-only
git diff swarm/<slug>/pre-wave-<N>..swarm/<slug>/post-wave-<N>
```

Also read the current state of every file that is both (a) listed in the diff and (b) relevant to the contract (referenced in Models, File Structure, or Patterns sections).

**Output 1 — Micro-review**

Check the merged code for:

1. **Contract compliance:** For each modified file, does it follow the contract?
   - Models: do implemented model shapes match the contract's Models section? Are all required fields present with correct types?
   - File locations: are files in the directories the contract's File Structure section specifies?
   - API patterns: do routes follow the contract's API shape (error format, pagination, auth guard)?
   - Patterns: is the repository pattern / validation approach / auth guard applied as the contract defines?

2. **Conflict scan:** Search for duplicate utilities or conflicting exports across the wave's features:

```bash
git diff swarm/<slug>/pre-wave-<N>..swarm/<slug>/post-wave-<N> \
  | grep "^+export " | sort | uniq -d
```

3. **Build health:**

```bash
<BUILD_CMD>
```

If the build fails, this is a major issue. Fix it.

Resolution:
- No issues: write "No issues found." Proceed.
- Minor issues (wrong file location, extra field not in contract, single naming inconsistency): fix directly on the base branch. Commit: `git add -- <files> && git commit -m "chore: wave-transition auto-fix for wave N"`
- Major issues (build broken, wrong auth pattern used across multiple files): fix what is possible. If unfixable without architectural changes, log a warning. Do not attempt fixes that would introduce new architectural decisions.

**Output 2 — Contract updates**

Read `docs/project-contract.md` in full. For each section:

- **Models:** Compare each defined model against its implementation. If a field was added by the feature and it makes semantic sense (e.g., `role: string` was added to User by the auth feature), add it to the contract. If a field type changed, update it.
- **File Structure:** Verify each path rule against where files actually landed. If files consistently land in a different directory than what the contract says, update the contract to match reality.
- **Patterns:** If the implementation uses the correct pattern but names it differently, update the contract to match the actual naming.
- **API:** If the base path, error shape, or pagination shape changed from the contract, update the contract.

Hard constraint: Updates are additive or corrective only. Never remove a model, field, or pattern that a previous wave already implemented. If an update would contradict an earlier wave's implementation, log it as a warning instead.

If any updates were made, commit:

```bash
git add -- docs/project-contract.md
git commit -m "docs: update contract after wave N — <brief summary of changes>"
```

If no updates were needed, do not commit.

**Output 3 — Wave learnings**

Append to `docs/wave-learnings.md` under a `## Wave N` heading. Use the format from section 21. Cover only observations that are factually true and would help future agents avoid problems or misunderstandings.

If `docs/wave-learnings.md` does not yet exist, create it with this first line:

```
# Wave Learnings
```

Then append the Wave N section.

Commit:

```bash
git add -- docs/wave-learnings.md
git commit -m "docs: add wave N learnings"
```

If a wave produced no learnings, write:

```markdown
## Wave N

_No significant learnings this wave._
```

**Completion signal**

After all three outputs are complete, print this block exactly. The `/swarm` command parses it:

```
WAVE_TRANSITION_COMPLETE
ISSUES_FOUND: N
ISSUES_AUTO_FIXED: N
MAJOR_WARNINGS: N
CONTRACT_UPDATES: N
LEARNINGS_ADDED: N
```

### Input/output contract

- Input: wave number, plan slug, merged/failed workbranch lists, file paths, build/test/lint commands — all provided in the invocation prompt
- Output: may modify `docs/project-contract.md`, appends to `docs/wave-learnings.md`, may commit minor fixes to base branch
- Prints `WAVE_TRANSITION_COMPLETE` block for caller to parse

### Allowed tools

`Edit, Write, Read, Glob, Grep, Bash`

---

## 9. New Skill: integration-reviewer

**File:** `develop-plugin/skills/integration-reviewer/SKILL.md`

The skill uses the same frontmatter style as `autonomous-feature-developer/SKILL.md` — name and description only, no other fields.

### YAML frontmatter

```yaml
---
name: integration-reviewer
description: "Use after all swarm waves complete. Reviews the entire merged codebase against the original plan, final contract, and wave learnings. Checks: (1) completeness — every plan feature has corresponding code, (2) cross-wave consistency — features from different waves interact correctly, (3) remaining contract compliance, (4) utility and component duplication across features, (5) dead code and leftover placeholders. Opens a cleanup PR with fixes. Trigger after /swarm finishes all waves."
---
```

### Skill body

**Requirements**

```markdown
## Requirements

- Git with branch and PR support
- Git hosting CLI — `gh` (GitHub) or `glab` (GitLab)
- Access to docs/project-context.md, docs/project-contract.md, and the swarm state file
```

**Input**

The caller provides in the invocation prompt:
- `PLAN_FILE` — relative path to the original plan
- `CONTRACT_FILE` — `docs/project-contract.md`
- `LEARNINGS_FILE` — `docs/wave-learnings.md` (may not exist)
- `MERGED_PR_URLS` — one URL per line, from `wave_results` where status is `"merged"`
- `FAILED_FEATURES` — comma-separated list of failed/blocked workbranch names, or `"none"`
- `BASE_BRANCH`, `BUILD_CMD`, `PR_CLI`, `MERGE_STRATEGY` from project context

**Phase 1 — Orientation**

Read the plan, contract, and learnings in full. Read `git log --oneline --all | head -60` to understand the commit history. For each merged workbranch (identifiable by its feature branch name from the PR URLs), read its diff summary:

```bash
git log --oneline --all --decorate | head -60
```

**Phase 2 — Completeness check**

For each feature in the plan that is NOT listed in `FAILED_FEATURES`:
- Search the codebase for code corresponding to the feature using its name and key terms from the description
- If no corresponding code is found, flag as `MISSING: <feature name>`

Document findings before moving on.

**Phase 3 — Cross-wave consistency**

For each pair of features from different waves where the later feature depends on the earlier:
- Find the Wave N feature's primary export (model, API route, utility function)
- Find the Wave N+1 feature's import of that export
- Verify the import path resolves and the interface matches
- Flag any broken cross-wave dependencies

**Phase 4 — Contract compliance**

Read the final `docs/project-contract.md`. For each section:
- **Models:** Grep for the implementation of each defined model. Verify field names and types match.
- **File Structure:** Verify files are where the contract says they should be.
- **Patterns:** Spot-check 3–5 features for correct pattern usage.
- **API:** Check a sample of route files for error format, auth guard usage, and pagination shape.

Skip findings that are already noted in `docs/wave-learnings.md` as contract corrections.

**Phase 5 — Duplication scan**

```bash
# Find exported names that appear in multiple files
grep -rn "^export function\|^export const\|^export default function" src/ \
  | awk -F: '{print $NF}' | sort | uniq -d
```

Flag any duplicate implementations. Determine which is canonical (the one whose file location matches the contract's File Structure section).

**Phase 6 — Dead code scan**

```bash
grep -rn "TODO\|FIXME\|PLACEHOLDER\|// stub\|# stub" src/ | head -30
```

Also identify large commented-out blocks (more than 3 consecutive comment lines).

**Phase 7 — Create cleanup PR**

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

### Input/output contract

- Input: plan path, contract path, learnings path, merged PR list, failed feature list, build config
- Output: opens a cleanup PR, prints `INTEGRATION_REVIEW_PR_URL=<url or "none">`

---

## 10. Modified Command: /auto-dev

**File:** `develop-plugin/commands/auto-dev.md`

### What stays the same

All YAML frontmatter fields are identical. Step 1 (environment check with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`) is identical. Step 3 (invoke `autonomous-feature-developer` skill) is identical. The Done table is identical.

### What changes — Step 2

Replace the current Step 2 body entirely with:

```markdown
## Step 2 — Get the feature request

The input is: **$ARGUMENTS**

**Determine input type:**

**Case 1 — Workbranch file:** If `$ARGUMENTS` is non-empty and ends with `.md`, check whether the file exists and has `# Workbranch:` as its first line:

```bash
FILE_FIRST_LINE=$(head -1 "$ARGUMENTS" 2>/dev/null)
```

If `FILE_FIRST_LINE` starts with `# Workbranch:`, this is a swarm invocation. Extract:

- `FEATURE_DESCRIPTION` — the full text of the `## Description` section
- `WORKBRANCH_SUBFEATURES` — the numbered list from the `## Sub-features` section (preserve all lines including numbers and descriptions)
- `WORKBRANCH_SLUG` — the filename without the `.md` extension (basename only)
- `PLAN_SLUG` — from the `## Context` section's `Plan:` field: extract the path, get `basename $(dirname $(dirname <plan-path>))` — i.e., the plan slug is the `<slug>` in `docs/workbranches/<slug>/`
- `WORKBRANCH_FILE` — the full path as provided in `$ARGUMENTS`

**Case 2 — Free-text description:** `$ARGUMENTS` is non-empty but is not a workbranch file. Set `FEATURE_DESCRIPTION="$ARGUMENTS"`. Set `WORKBRANCH_FILE=""`, `WORKBRANCH_SUBFEATURES=""`, `WORKBRANCH_SLUG=""`, `PLAN_SLUG=""`.

**Case 3 — Empty:** Ask the user: "What feature would you like to build?"
```

### What changes — Step 3 addendum

After the existing Step 3 instruction, add:

```markdown
If `WORKBRANCH_FILE` is non-empty (swarm invocation), pass these additional variables to the skill:

- `WORKBRANCH_FILE` — the workbranch file path
- `WORKBRANCH_SLUG` — the workbranch slug
- `PLAN_SLUG` — the plan slug
- `WORKBRANCH_SUBFEATURES` — the sub-features list
- `PHASE1_SYNC` — set to `"true"`

In swarm invocations, the skill must skip Phase 4.5 (Merge). The /swarm command manages
all merging via the sequential merge queue. The skill runs Phases 0–4 (setup, architecture,
implementation, PR creation, review loop), then writes the done marker (Phase 5.5), then
runs Phase 5 (cleanup). It does NOT merge the PR.
```

### Backward compatibility

The workbranch file detection requires: (a) argument ends in `.md`, (b) file exists, (c) first line is `# Workbranch:`. A free-text feature description cannot satisfy all three conditions. All existing usages of `/auto-dev <free text>` are unaffected.

---

## 11. Modified Skill: autonomous-feature-developer/SKILL.md

**File:** `develop-plugin/skills/autonomous-feature-developer/SKILL.md`

### What stays the same

The name, description, and Requirements section. The Pipeline Overview table. All of Phase 0 (Setup). All of Phase 2 (Implementation). All of Phase 3 (Pull Request). All of Phase 4 (Review and Fix Loop). All of Phase 4.5 (Merge) — with one conditional note added (see below). All of Phase 5 (Cleanup). The Done report table. The Aborting and Recovery section.

### What changes — Context File section

Add two rows to the existing Context File variable extraction table:

| Variable | Context file location | Default |
|---|---|---|
| `CONTRACT_FILE` | Derived: `docs/project-contract.md` at `$REPO_ROOT` | `docs/project-contract.md` |
| `LEARNINGS_FILE` | Derived: `docs/wave-learnings.md` at `$REPO_ROOT` | `docs/wave-learnings.md` |

Add a note after the table: "These files may not exist for standalone `/auto-dev` invocations. The skill checks for their existence before reading them — missing files are skipped silently."

### What changes — New section: Swarm Context

Insert this section after the Context File section, before Phase 0:

```markdown
## Swarm Context

When invoked via `/swarm`, additional variables are passed:

| Variable | Meaning |
|---|---|
| `WORKBRANCH_FILE` | Path to the workbranch file for this feature |
| `WORKBRANCH_SLUG` | Slug of this workbranch (filename without .md) |
| `PLAN_SLUG` | Slug of the parent plan |
| `WORKBRANCH_SUBFEATURES` | Newline-separated list of sub-feature descriptions from the workbranch file |
| `PHASE1_SYNC` | `"true"` — agent must perform Phase 1 sync point protocol |

If `WORKBRANCH_FILE` is empty, this is a standalone invocation. All swarm-specific steps are no-ops.
```

### What changes — Phase 1 reference

The additions to Phase 1 are in `phase-1-architecture.md` (section 12). The SKILL.md Pipeline Overview table already points to that reference file, so no change to the table is needed. However, add this note to the Phase 1 line in the pipeline table:

Change the Phase 1 Reads column from `references/phase-1-architecture.md` to `references/phase-1-architecture.md, docs/project-contract.md (if exists), docs/wave-learnings.md (if exists, wave 2+)`

### What changes — Phase 4.5 conditional

Add this note to the Phase 4.5 (Merge) section:

```markdown
**Swarm invocation only:** If `WORKBRANCH_FILE` is non-empty, skip Phase 4.5 entirely.
The /swarm command manages all merging via the sequential merge queue. Proceed directly
to Phase 5.5 (Write done marker), then Phase 5 (Cleanup).
```

### What changes — New Phase 5.5

Insert this section between Phase 5 (Cleanup) and the Done table:

```markdown
## Phase 5.5 — Write done marker (swarm invocation only)

If `WORKBRANCH_FILE` is empty, skip this phase.

Write the done marker before performing Phase 5 cleanup. Path:

```
docs/workbranches/$PLAN_SLUG/$WORKBRANCH_SLUG-done.json
```

On success (review loop completed, PR open and ready to merge):

```json
{
  "workbranch": "<WORKBRANCH_SLUG>",
  "status": "merged",
  "pr_url": "<PR_URL>",
  "pr_number": "<PR_NUMBER>",
  "merged": false,
  "branch": "<BRANCH>",
  "worktree": "<WORKTREE>",
  "review_iterations": <N>,
  "contract_deviations": ["<deviation description if any, or empty array>"]
}
```

Note: `"merged": false` because `/swarm` handles merging. Status `"merged"` here means "ready to merge — PR is open, review loop complete."

On failure (any phase failed to complete):

```json
{
  "workbranch": "<WORKBRANCH_SLUG>",
  "status": "failed",
  "pr_url": "<PR_URL or empty string>",
  "pr_number": "<PR_NUMBER or empty string>",
  "merged": false,
  "branch": "<BRANCH>",
  "worktree": "<WORKTREE>",
  "review_iterations": <N>,
  "contract_deviations": [],
  "error": "<one to two sentence summary of what failed and why>"
}
```

Write the done marker even if Phase 5 cleanup subsequently fails.
```

### Backward compatibility

All new steps check for `WORKBRANCH_FILE` being non-empty or for the relevant files existing before doing anything. Standalone invocations with no workbranch file and no contract file follow exactly the same path as v1.0.0.

---

## 12. Modified Reference: phase-1-architecture.md

**File:** `develop-plugin/skills/autonomous-feature-developer/references/phase-1-architecture.md`

### What stays the same

The Goal line. All existing Steps 1–5. The Plan Template. All Guidelines.

### What changes — new Steps 3a, 3b, 3c

Insert these three steps between the existing Step 3 (Explore the codebase) and Step 4 (Write the plan):

```markdown
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
```

### What changes — new Step 5a

Insert this step after the existing Step 5 (Commit the plan):

```markdown
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
```

### What changes — Guidelines addition

Add this bullet to the Guidelines section:

```markdown
- If the project contract (`docs/project-contract.md`) defines a model, API shape, or
  file location relevant to this feature, those definitions are hard constraints. Your
  plan must be compatible with them. Note any incompatibilities you discover in the
  Architecture Decisions section with the label "CONTRACT DISCREPANCY:".
```

### What changes — review-rubric.md addition

Add one bullet to `references/review-rubric.md` under the **Conventions Compliance** section:

```markdown
- **Contract compliance:** Do all new files follow the project contract's model shapes,
  API error format, file locations, and coding patterns? Reference `docs/project-contract.md`.
  Check each contract section that is relevant to this feature.
```

---

## 13. Modified Command: /init

**File:** `develop-plugin/commands/init.md`

### What stays the same

All YAML frontmatter fields. All existing steps (whatever they currently are). The existing Next Steps summary.

### What changes — New Step 3.5

Insert this step after the existing step that copies the project context template and before the existing gitignore step:

```markdown
## Step 3.5 — Create swarm directory structure

Create the directories used by /plan, /import-plan, and /swarm:

```bash
mkdir -p docs/plans
mkdir -p docs/workbranches
mkdir -p docs/reports
```

These directories are safe to create unconditionally — `mkdir -p` is idempotent on existing directories.

Then check whether `docs/` would be gitignored:

```bash
git check-ignore -q docs/ 2>/dev/null && echo "DOCS_IGNORED=yes" || echo "DOCS_IGNORED=no"
```

If `DOCS_IGNORED=yes`, warn the user:

```
Note: docs/ is gitignored. Plans, contracts, and reports written by /plan and /swarm
will not be committed to the repository. If you want them tracked, remove docs/ from
.gitignore or add an exception: !docs/plans/ !docs/reports/ !docs/project-contract.md
```
```

### What changes — Next Steps update

Update the Next Steps section in the final summary to include the swarm workflow:

```
Next steps:
  1. Fill in docs/project-context.md with your project's stack, build commands, and conventions
  2a. Single feature:    /auto-dev <feature description>
  2b. Full platform:     /plan   — brainstorm and structure a plan interactively
                      →  /swarm docs/plans/<your-plan>.md   — build the platform
```

### Backward compatibility

`mkdir -p` on existing directories is a no-op. The gitignore check produces a warning only — no file is modified. All existing `/init` behavior is preserved.

---

## 14. Scripts — New and Modified

### 14.1 Modified: setup.sh

**File:** `develop-plugin/skills/autonomous-feature-developer/scripts/setup.sh`

**Change summary:** Accept an optional third argument `CONTRACT_FILE_ARG`. Validate it if provided. Add `CONTRACT_FILE=...` to the output.

**Exact changes to the script:**

After line 11 (`CONTEXT_FILE_ARG="${2:-}"`) add:

```bash
CONTRACT_FILE_ARG="${3:-}"
```

After the existing context file validation block (the `if [ ! -f "$CONTEXT_FILE" ]` block), add:

```bash
# Validate contract file if specified (swarm context); non-fatal if not specified
if [ -n "$CONTRACT_FILE_ARG" ]; then
  if [ ! -f "$CONTRACT_FILE_ARG" ]; then
    echo "ERROR: contract file not found: ${CONTRACT_FILE_ARG}" >&2
    echo "  Run /plan or /import-plan to generate it." >&2
    exit 1
  fi
  CONTRACT_FILE="$CONTRACT_FILE_ARG"
else
  # Default location — not validated (optional for standalone auto-dev)
  CONTRACT_FILE="${REPO_ROOT}/docs/project-contract.md"
fi
```

After the final existing `echo "CONTEXT_FILE=${CONTEXT_FILE}"` line, add:

```bash
echo "CONTRACT_FILE=${CONTRACT_FILE}"
```

**Interface after change:**

```
Usage: bash setup.sh "<feature request text>" [context-file-path] [contract-file-path]
Output (all existing lines preserved, one new line added):
  SLUG=...
  BRANCH=...
  WORKTREE=...
  PLAN_FILE=...
  CONTEXT_FILE=...
  CONTRACT_FILE=...    <- new
```

**What stays the same:** All existing argument handling, slug derivation, worktree creation, idempotency logic, and all other output lines.

### 14.2 New script: swarm-rebase-merge.sh

**File:** `develop-plugin/skills/autonomous-feature-developer/scripts/swarm-rebase-merge.sh`

**Full script content:**

```bash
#!/usr/bin/env bash
# swarm-rebase-merge.sh — Rebase a feature branch onto the updated base branch
# and merge its PR. Used by the /swarm sequential merge queue.
#
# Usage:
#   bash swarm-rebase-merge.sh <worktree> <branch> <base-branch> \
#     <pr-number> <pr-cli> <merge-strategy> <repo-root>
#
# Arguments:
#   worktree        — absolute path to the feature's worktree
#   branch          — feature branch name (e.g. feature/auth)
#   base-branch     — branch to rebase onto (e.g. main)
#   pr-number       — PR/MR number to merge after successful rebase
#   pr-cli          — "gh" or "glab"
#   merge-strategy  — "--squash", "--rebase", or "--merge"
#   repo-root       — absolute path to the main repository
#
# Exit codes:
#   0  — rebased and merged successfully
#   1  — rebase conflict (caller must resolve or mark as failed)
#   2  — merge CLI failure (network, auth, permissions, etc.)
#   3  — push rejected (force-with-lease race condition — retry once)
#
# IMPORTANT: This script uses git push --force-with-lease. The default
# permissions deny list includes "Bash(git push --force*)". You must either:
# (A) Add "Bash(git push --force-with-lease*)" to permissions.allow in
#     .claude/settings.local.json (allow overrides deny for same pattern), or
# (B) Replace the push step with: git push origin --delete "$BRANCH" && git push origin "$BRANCH"
# Document your chosen approach here before shipping.

set -uo pipefail

WORKTREE="${1:?Usage: swarm-rebase-merge.sh <worktree> <branch> <base-branch> <pr-number> <pr-cli> <merge-strategy> <repo-root>}"
BRANCH="${2:?}"
BASE_BRANCH="${3:?}"
PR_NUMBER="${4:?}"
PR_CLI="${5:?}"
MERGE_STRATEGY="${6:---squash}"
REPO_ROOT="${7:?}"

# Fetch latest state of the base branch
git -C "$REPO_ROOT" fetch origin "$BASE_BRANCH"

# Perform rebase in the feature worktree
cd "$WORKTREE"
if ! git rebase "origin/${BASE_BRANCH}"; then
  echo "REBASE_CONFLICT: ${BRANCH}" >&2
  echo "CONFLICT_FILES:"
  git diff --name-only --diff-filter=U
  git rebase --abort
  exit 1
fi

# Push the rebased branch
if ! git push --force-with-lease origin "$BRANCH"; then
  echo "PUSH_REJECTED: ${BRANCH}" >&2
  exit 3
fi

# Merge the PR/MR
case "$PR_CLI" in
  gh)
    if gh pr merge "$PR_NUMBER" "$MERGE_STRATEGY" --delete-branch 2>&1; then
      echo "MERGED: PR #${PR_NUMBER}"
      exit 0
    else
      echo "MERGE_FAILED: PR #${PR_NUMBER}" >&2
      exit 2
    fi
    ;;
  glab)
    GLAB_FLAGS="--remove-source-branch"
    case "$MERGE_STRATEGY" in
      --squash) GLAB_FLAGS="$GLAB_FLAGS --squash" ;;
      --rebase) GLAB_FLAGS="$GLAB_FLAGS --rebase" ;;
      # --merge is glab default, no flag needed
    esac
    # shellcheck disable=SC2086  # GLAB_FLAGS is intentionally word-split
    if glab mr merge "$PR_NUMBER" $GLAB_FLAGS 2>&1; then
      echo "MERGED: MR !${PR_NUMBER}"
      exit 0
    else
      echo "MERGE_FAILED: MR !${PR_NUMBER}" >&2
      exit 2
    fi
    ;;
  *)
    echo "ERROR: unsupported PR CLI '${PR_CLI}'. Use 'gh' or 'glab'." >&2
    exit 2
    ;;
esac
```

### 14.3 No changes to other scripts

`verify.sh`, `create-pr.sh`, and `merge-cleanup.sh` are invoked exactly as before. No changes.

---

## 15. Templates

### 15.1 New template: project-contract.template.md

**File:** `develop-plugin/skills/autonomous-feature-developer/assets/project-contract.template.md`

This template is referenced by `/plan` and `/import-plan` as a structural guide when generating the contract. The commands generate contract content matching this structure — they do not copy the template verbatim.

**Full file content:**

```markdown
# Project Contract

> This file is read by every auto-dev agent in the swarm.
> It contains hard constraints. Every agent follows every rule here exactly.
>
> How to fill this in:
> - Remove every section that does not apply to your project
> - Do not write "N/A", "optional", "TBD", or leave placeholder text
> - No prose, no examples, no explanations — only definitions
> - Omit a section entirely rather than writing an empty one
>
> Audience: machines, not humans.

---

## Models

<!-- Define every shared data model used by multiple features.
     Feature-local models go in the feature code, not here.
     Use TypeScript interfaces or your language's equivalent. -->

```typescript
interface ExampleModel {
  id: string         // uuid, generated on create
  name: string       // required, max 255 chars
  createdAt: Date    // set by ORM on insert, not writable by API
}
```

---

## API

<!-- One definitive value per line. No ranges, no "or", no optionality. -->

- Style: REST
- Base path: /api/v1
- Auth mechanism: JWT in httpOnly cookie
- Auth middleware location: src/middleware/auth.ts
- Error shape: `{ error: string, code: number }`
- Pagination: `{ data: T[], nextCursor: string | null }`

---

## File Structure

<!-- Define where each category of file lives. Paths are relative to project root.
     These become hard constraints — every agent follows them. -->

- Routes: src/routes/<resource>.ts
- Models: src/models/<name>.ts
- Middleware: src/middleware/<name>.ts
- Utils: src/lib/<name>.ts
- Shared types: src/types/<domain>.ts

---

## Patterns

<!-- Define implementation patterns all features must follow.
     Only include patterns that apply to multiple features. -->

- Database access: repository pattern — no raw queries in route handlers
- Repository location: src/repositories/<model>.ts
- Validation: Zod schema defined in route file, exported as <Resource>Schema
- Auth guard: requireAuth() middleware wrapping all protected routes
- Type exports: define in src/types/<domain>.ts, re-export from src/types/index.ts

---

## Dependencies

<!-- List shared dependencies with version constraints where they matter. -->

- ORM: Prisma 5.x
- Validation: Zod 3.23+
- Auth: jsonwebtoken 9.x
```

### 15.2 Existing template: project-context.template.md

No changes. The file at `develop-plugin/skills/autonomous-feature-developer/assets/project-context.template.md` is unchanged.

---

## 16. Swarm State Schema and File Lifecycle

**File location (in the user's project, written by `/swarm`):**
`docs/workbranches/<plan-slug>/swarm-state.json`

### Schema

```typescript
interface SwarmState {
  // Identity
  plan: string;               // relative path to plan file
                              // e.g. "docs/plans/my-platform-plan.md"
  plan_slug: string;          // e.g. "my-platform"
  contract_hash: string;      // MD5 or SHA-1 of docs/project-contract.md content
                              // at swarm start — for detecting mid-swarm edits
  started_at: string;         // ISO 8601 timestamp
  updated_at: string;         // ISO 8601 timestamp of last write

  // Progress
  status: "running" | "halted" | "completed";
  halt_reason?: string;       // present only when status === "halted"
  current_wave: number;       // wave currently executing, or next wave to execute on resume
  waves_completed: number[];  // wave numbers that have fully completed

  // Per-wave results — outer key is wave number as string (JSON requires string keys)
  wave_results: {
    [waveNumber: string]: {
      [workbranchSlug: string]: "merged" | "failed" | "blocked";
    };
  };

  // Failure tracking
  failed_features: string[];   // workbranch slugs with status "failed"
  blocked_features: string[];  // workbranch slugs blocked by a failed dependency

  // Git rollback points (in creation order)
  tags: string[];

  // Final outputs
  integration_pr_url?: string; // URL of cleanup PR, set after final integration review
  report_path?: string;        // relative path to final report file
}
```

### Initial value written at swarm start

```json
{
  "plan": "docs/plans/my-platform-plan.md",
  "plan_slug": "my-platform",
  "contract_hash": "<sha1 of contract content>",
  "started_at": "2026-03-14T10:00:00Z",
  "updated_at": "2026-03-14T10:00:00Z",
  "status": "running",
  "current_wave": 1,
  "waves_completed": [],
  "wave_results": {},
  "failed_features": [],
  "blocked_features": [],
  "tags": []
}
```

### File lifecycle

| Event | State change |
|---|---|
| Swarm starts (fresh) | File created with initial values |
| Wave N agents dispatched | No change |
| Phase 1 sync complete | No change |
| All agents in wave N finish | No change |
| Merge queue complete for wave N | `wave_results[N]` populated with per-workbranch statuses |
| Post-wave tag created | Tag appended to `tags` array |
| Wave-transition complete | No change (wave-transition manages its own files) |
| Wave N fully complete | N added to `waves_completed`; `current_wave` = N+1; `updated_at` refreshed |
| Feature fails | Slug added to `failed_features`; dependent slugs added to `blocked_features` |
| Halt condition triggers | `status = "halted"`; `halt_reason` set; `updated_at` refreshed |
| All waves complete | No change yet |
| Integration PR opened | `integration_pr_url` set |
| Final report written | `report_path` set; `status = "completed"` |
| User chooses "fresh" on resume | File deleted and recreated from scratch |

### Resume contract

When the file exists with `status === "halted"` or `status === "running"`:

- Skip Steps 4–8 (validation, decomposition, graph build, execution plan print)
- Load `failed_features`, `blocked_features`, `wave_results`, `waves_completed`, `tags` from file
- Start the wave loop from `current_wave`
- In Step 10c, filter out workbranches in `failed_features` or `blocked_features` before dispatching
- Previously created git tags are still in place and valid

---

## 17. Wave Execution Engine — Agent Dispatch Contracts

### Dispatching auto-dev agents

Each auto-dev agent for a workbranch is invoked via the Agent tool.

**Agent tool parameters:**

```
tools: ["Edit", "Write", "Glob", "Grep", "Read", "NotebookEdit", "Bash"]
```

**Prompt template** (substitute angle-bracket placeholders with actual values):

```
You are an autonomous feature developer. Build the feature defined in the workbranch
file below. Run it to completion without pausing for input.

## Workbranch file
Path: <WORKBRANCH_FILE_PATH>
Read this file first.

## Variables
WORKBRANCH_FILE=<WORKBRANCH_FILE_PATH>
WORKBRANCH_SLUG=<WORKBRANCH_SLUG>
PLAN_SLUG=<PLAN_SLUG>
PHASE1_SYNC=true

## Sub-features (Implementation Order seed)
<PASTE THE FULL NUMBERED SUB-FEATURES LIST FROM THE WORKBRANCH FILE>

## Instructions

Invoke the autonomous-feature-developer skill. Execute all phases in order:

Phase 0: Pass the workbranch's Description as the feature request to setup.sh.
Phase 1: Use the Sub-features above as your Implementation Order seed.
         Read docs/project-contract.md (required).
         Read docs/wave-learnings.md if it exists.
         After committing your plan, perform the Phase 1 sync point protocol.
         See references/phase-1-architecture.md Step 5a.
Phase 2: Implement according to the plan. Follow the contract for all shared concerns.
Phase 3: Create the PR.
Phase 4: Run the review and fix loop.
Phase 4.5: SKIP. Do not merge the PR. /swarm handles merging.
Phase 5.5: Write the done marker file. See SKILL.md Phase 5.5.
Phase 5: Run cleanup.
```

**Parallelism note:** All agents in a wave are dispatched concurrently. The `/swarm` command does not wait for agent N to finish before dispatching agent N+1.

### Dispatching the decomposer agent

**Agent tool parameters:**

```
tools: ["Read", "Write", "Glob", "Grep", "Bash"]
```

**Prompt template:**

```
You are the decomposer agent. Decompose the following plan into workbranch files.

## Plan document
<FULL TEXT CONTENT OF PLAN FILE>

## Project contract
<FULL TEXT CONTENT OF docs/project-contract.md>

## Project context
<FULL TEXT CONTENT OF docs/project-context.md>

## Parameters
PLAN_SLUG=<PLAN_SLUG>
IS_EXISTING_PROJECT=<"true" or "false">

## Instructions
Follow the decomposer agent instructions in full.
Write workbranch files to: docs/workbranches/<PLAN_SLUG>/
Print the decomposition summary when done.
```

### Dispatching the integration-reviewer skill

**Agent tool parameters:**

```
tools: ["Edit", "Write", "Read", "Glob", "Grep", "Bash"]
```

**Prompt template:**

```
You are the integration reviewer. Run a final review of the fully merged codebase.

## Parameters
PLAN_FILE=<PLAN_FILE_PATH>
CONTRACT_FILE=docs/project-contract.md
LEARNINGS_FILE=docs/wave-learnings.md
BASE_BRANCH=<BASE_BRANCH>
BUILD_CMD=<BUILD_CMD>
TEST_CMD=<TEST_CMD or empty string>
LINT_CMD=<LINT_CMD or empty string>
PR_CLI=<PR_CLI>
MERGE_STRATEGY=<MERGE_STRATEGY>

## Merged PR URLs
<ONE URL PER LINE — from wave_results where status === "merged">

## Failed and blocked features
<COMMA-SEPARATED LIST OF SLUGS, or "none">

## Instructions
Follow the integration-reviewer skill in full. End your response with:
INTEGRATION_REVIEW_PR_URL=<url or "none">
```

---

## 18. Phase 1 Sync Point Mechanism

All sync files for a swarm run live in `docs/workbranches/<plan-slug>/`.

### Step-by-step protocol

**Each auto-dev agent (after committing its Phase 1 plan):**

1. Writes `<workbranch-slug>-phase1-report.json`:

```json
{
  "workbranch": "<workbranch-slug>",
  "phase1_complete": true,
  "files_to_create": [
    "src/routes/auth.ts",
    "src/models/user.ts"
  ],
  "files_to_modify": [
    "src/types/index.ts"
  ]
}
```

2. Polls for `<workbranch-slug>-phase1-resolution.json` every 30 seconds.

3. Timeout: 10 minutes. On timeout, the agent fails with: "ERROR: Phase 1 sync timeout after 600s"

**The /swarm orchestrator (after dispatching all agents for the wave):**

1. Polls every 60 seconds for all `<workbranch-slug>-phase1-report.json` files for the wave.

2. Timeout: 20 minutes. Any workbranch that has not produced a report by then is marked failed: "Phase 1 report timeout."

3. Once all reports are collected, build the conflict map:

```
file_path → [workbranch_slug, ...]
```

4. For each file with more than one claimant, resolve:

   a. Read both workbranch files. Read the contract's File Structure section.

   b. Determine which workbranch has the stronger claim (whose feature description is more directly about this resource type — e.g., the auth workbranch has a stronger claim over `src/models/user.ts` than the dashboard workbranch).

   c. The stronger-claim workbranch keeps the file. The other workbranch gets this file added to its `reassigned_files`.

   d. If both workbranches have equally strong claims (both features genuinely need to write to the same file, e.g., both add exports to `src/types/index.ts`): sequence them. Higher-priority workbranch proceeds first. Lower-priority workbranch gets `wait_for` set to the higher-priority slug.

5. Writes one resolution file per agent:

No-conflict example:
```json
{
  "workbranch": "auth",
  "proceed": true,
  "reassigned_files": [],
  "wait_for": null
}
```

Conflict example (auth wins the file):
```json
{
  "workbranch": "dashboard",
  "proceed": true,
  "reassigned_files": ["src/types/index.ts"],
  "wait_for": null
}
```

Sequencing example (both need the file, dashboard waits for auth):
```json
{
  "workbranch": "dashboard",
  "proceed": true,
  "reassigned_files": [],
  "wait_for": "auth"
}
```

### wait_for polling behavior in the agent

After receiving `wait_for: "auth"`, the agent polls for `docs/workbranches/<plan-slug>/auth-done.json` every 60 seconds. Timeout: 60 minutes.

When the file appears:
- If `status === "merged"` (ready to merge): proceed to Phase 2.
- If `status === "failed"`: mark this workbranch as failed with reason: "wait_for dependency `auth` failed."

---

## 19. Sequential Merge Queue

### Algorithm

After all done markers for a wave are present (or the 60-minute agent timeout is reached), `/swarm` runs:

```
sort workbranches by: priority (high → medium → low) then alphabetical

for each workbranch in sorted order:

  1. read done marker
     if status === "failed": record "failed" in swarm state, skip

  2. call:
     bash swarm-rebase-merge.sh \
       <worktree> <branch> <base-branch> \
       <pr-number> <pr-cli> <merge-strategy> <repo-root>

  3. exit 0 → record "merged" in swarm state, continue to next

  4. exit 1 (conflict) → run conflict resolution (see below)

  5. exit 2 (CLI failure) → record "failed" with error "merge CLI failure", continue

  6. exit 3 (push rejected) → wait 5 seconds, retry once
     if retry fails → record "failed" with error "push rejected after rebase", continue
```

### Orchestrator conflict resolution (exit 1)

The script outputs `CONFLICT_FILES:` followed by one conflicting path per line. For each conflicting file:

1. Read the file at HEAD (current base branch state after prior merges in this queue): `git show HEAD:<file>`
2. Read the file from the feature branch: `git show <branch>:<file>`
3. Read both workbranch files for intent.
4. Read the contract for the canonical version of any model or pattern.

Resolution rules (apply in order, first match wins):

| File type | Resolution |
|---|---|
| Shared type file (`src/types/*.ts`, similar) | Merge both sets of additions — both features added different exports, keep both |
| Config file (`package.json`, `.env.example`, etc.) | Merge additive changes; for conflicting values, use the base branch version |
| Model/schema file | Use higher-priority workbranch's version (it merged first, it is ground truth). Log the decision in wave learnings. |
| Any other file | If the conflict is purely additive (both add non-overlapping content), merge both. Otherwise, use higher-priority workbranch's version. |
| Unresolvable | Abort rebase: `git rebase --abort`. Record "failed" with error "unresolvable merge conflict in `<file>` — manual resolution required". Continue queue. |

After applying resolution:

```bash
# For each resolved file:
git add -- <file>
git rebase --continue
git push --force-with-lease origin <branch>
# Then proceed with PR merge
```

### Done marker schema

Written by each auto-dev agent at Phase 5.5. Read by the merge queue to get `pr_number`, `branch`, and `worktree`.

```typescript
interface WorkbranchDone {
  workbranch: string;            // workbranch slug
  status: "merged" | "failed";   // "merged" = PR is open and ready; "failed" = cannot proceed
  pr_url: string;                // PR URL (empty string if PR was never created)
  pr_number: string;             // PR number (empty string if PR was never created)
  merged: boolean;               // always false in swarm context (swarm handles merging)
  branch: string;                // feature branch name, e.g. "feature/auth"
  worktree: string;              // absolute path to worktree
  review_iterations: number;     // how many review iterations were completed
  contract_deviations: string[]; // descriptions of contract deviations, or []
  error?: string;                // present when status === "failed"
}
```

---

## 20. Wave-Transition Agent Invocation Contract

### Invocation prompt

After tagging `post-wave-N`, `/swarm` invokes the wave-transition agent:

**Agent tool parameters:**

```
tools: ["Edit", "Write", "Read", "Glob", "Grep", "Bash"]
```

**Prompt template:**

```
You are the wave-transition agent. Run a single-pass post-wave review for Wave <N>.

## Parameters
WAVE_NUMBER=<N>
PLAN_SLUG=<PLAN_SLUG>
PRE_WAVE_TAG=swarm/<PLAN_SLUG>/pre-wave-<N>
POST_WAVE_TAG=swarm/<PLAN_SLUG>/post-wave-<N>
CONTRACT_FILE=docs/project-contract.md
LEARNINGS_FILE=docs/wave-learnings.md
BUILD_CMD=<BUILD_CMD>
TEST_CMD=<TEST_CMD or empty string>
LINT_CMD=<LINT_CMD or empty string>
BASE_BRANCH=<BASE_BRANCH>
PR_CLI=<PR_CLI>

## Merged workbranches this wave
<ONE WORKBRANCH SLUG PER LINE>

## Failed workbranches this wave
<ONE WORKBRANCH SLUG PER LINE, or the word "none">

## Instructions
Follow the wave-transition agent instructions exactly. Produce all three outputs
in a single pass: micro-review, contract updates, wave learnings.
End your response with the WAVE_TRANSITION_COMPLETE block.
```

### Parsing the completion signal

The `/swarm` command scans the agent's response for a line that is exactly `WAVE_TRANSITION_COMPLETE`. The lines immediately following it are parsed as key-value pairs:

```
WAVE_TRANSITION_COMPLETE
ISSUES_FOUND: 3
ISSUES_AUTO_FIXED: 2
MAJOR_WARNINGS: 1
CONTRACT_UPDATES: 1
LEARNINGS_ADDED: 4
```

Values are stored in the swarm state as annotations on `wave_results[N]`:

```json
"wave_results": {
  "1": {
    "auth": "merged",
    "config": "merged",
    "_transition": {
      "issues_found": 3,
      "issues_auto_fixed": 2,
      "major_warnings": 1,
      "contract_updates": 1,
      "learnings_added": 4
    }
  }
}
```

If the completion block is not found, `/swarm` logs: `WARN: wave-transition did not produce WAVE_TRANSITION_COMPLETE signal for wave N` and continues. The swarm does not halt on wave-transition failure.

---

## 21. File Formats Reference

### Plan document

Produced by `/plan` and `/import-plan`. Input to `/swarm` and the decomposer.

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

**Parsing rules:**
- Feature heading format: exactly `### Feature: <Name>` — three hashes, space, "Feature:", space, name
- `Description:`, `Dependencies:`, `Priority:` are label lines directly following the heading, one per line
- Feature names must be unique (case-insensitive comparison for validation, case-sensitive for dependency matching)
- Dependencies value: comma-separated names, or the single word `none`
- Priority value: `high`, `medium`, or `low` (case-insensitive); default `medium` if omitted

### Workbranch file

Produced by the decomposer. Read by `/swarm`, auto-dev agents, and the wave-transition agent.

```markdown
# Workbranch: <Name>

## Description
<Natural language description from the plan's Feature Description field>

## Sub-features
1. <Sub-feature name> — <one-line description: what files it touches and what they do>
2. <Sub-feature name> — <one-line description>
3. ...

## Owns (predicted)
- <file or directory path this workbranch expects to create or modify>
- <file or directory path>

## Dependencies
<comma-separated workbranch names, or "none">

## Priority
<high | medium | low>

## Wave
<integer>

## Context
- Platform: <platform name from plan>
- Plan: <relative path to plan file>
- Contract: docs/project-contract.md
- Learnings: docs/wave-learnings.md
- Base branch: <BASE_BRANCH from project context>
- Status: pending
```

**File naming:** `<workbranch-name-slug>.md`. Slug algorithm: lowercase → non-alphanumeric to hyphen → collapse consecutive hyphens → strip leading/trailing hyphens → truncate to 50 chars.

**Status field values:**
- `pending` — initial state set by decomposer
- `in-progress` — set by `/swarm` when the agent is dispatched (Step 10d)
- `merged` — set by `/swarm` after the PR successfully merges in the queue
- `failed` — set by `/swarm` after the agent fails or the PR cannot merge
- `blocked` — set by `/swarm` when a dependency is failed

The `/swarm` command updates the `Status:` field in the workbranch file in-place. Auto-dev agents read the workbranch file but do not modify it.

### Project contract

Full structure defined in section 15.1. The contract grows over time as wave-transition agents add corrections. The top-level heading is always `# Project Contract`. Sections are:

- `## Models`
- `## API`
- `## File Structure`
- `## Patterns`
- `## Dependencies`

Sections are omitted when they don't apply. No section appears more than once. Wave-transition agents may add new sections for stack-specific concerns discovered post-Wave 1 (e.g., `## Database` for Prisma-specific rules).

### Wave learnings

```markdown
# Wave Learnings

## Wave <N>

### Build
- <observation about build command behavior, ordering requirements, flags needed>

### Dependencies
- <package version requirement or version incompatibility discovered>

### Patterns discovered
- <what the codebase actually does vs what was expected or what the contract said>

### Contract corrections
- <model or path or pattern>: <what changed and why>
```

**Rules:**
- First line of file: `# Wave Learnings`
- Each wave uses `## Wave N` heading with incrementing N
- Sub-sections are optional — omit empty sub-sections entirely
- If no learnings: write `## Wave N` then `_No significant learnings this wave._`
- File is append-only — existing content is never edited after being written

### Final report

```markdown
# Swarm Report — <Platform Name>

**Date:** <ISO 8601 timestamp>
**Plan:** <relative path to plan file>
**Contract:** docs/project-contract.md
**Learnings:** docs/wave-learnings.md
**Duration:** <wall-clock time, e.g. "2h 14m">

## Summary

| Metric | Value |
|---|---|
| Features planned | N |
| Features merged | N |
| Features failed | N |
| Features blocked | N |
| Waves executed | N |
| Contract updates | N |
| Integration PR | <URL or "none needed"> |
| Rollback tags | swarm/<slug>/pre-wave-1 through post-wave-<N> |

## Wave Execution

### Wave <N>
- **Features:** <name> (merged), <name> (merged)
- **Merge order:** <name> → <name>
- **Phase 1 sync:** <"no ownership conflicts" or "N conflicts resolved: <description>">
- **Wave transition:** <N issues found>, <N auto-fixed>, <N warnings>, <N contract updates>, <N learnings>
- **Halt check:** <"N% blocked → continue" or "N% blocked → HALT">

## Features

### <Feature Name>
- **Status:** merged | failed | blocked
- **Wave:** N
- **Sub-features:** N completed / N planned
- **PR:** <URL>
- **Branch:** <branch name>
- **Review iterations:** N
- **Contract deviations:** <bulleted list or "none">
- **Notes:** <any issues or deviations from the plan>

## Integration Review
- **Issues found:** N
- **Issues fixed:** N
- **Contract deviations found:** N
- **Issues needing manual attention:** N
- **Cleanup PR:** <URL or "none">

## Failures and Blocked Features

### <Feature Name> (FAILED)
- **Wave:** N
- **Reason:** <build failure | review loop exhausted | merge conflict | Phase 1 sync timeout | agent timeout>
- **Last error:** <1–2 sentence summary>
- **Rollback tag:** swarm/<slug>/pre-wave-<N>

### <Feature Name> (BLOCKED)
- **Blocked by:** <failed feature name>
- **Transitively blocked by:** <root failed feature name, if chain is longer than one step>
```

---

## 22. Cross-Cutting Concerns

### Error handling table

| Error type | Handling |
|---|---|
| Plan file not found | Stop at Step 2, print path |
| Plan parse error (duplicate name, bad dep ref) | Stop at Step 4, print every error found |
| Circular dependency in plan | Stop at Step 4, print the cycle |
| Contract missing | Stop at Step 5, direct to /plan |
| Contract inconsistent | Stop at Step 5, list all inconsistencies, do not start swarm |
| Context missing | Stop at Step 6, direct to /init |
| Build command missing from context | Stop at Step 6 |
| Agent timeout (60 min, no done marker) | Mark workbranch failed, continue |
| Phase 1 report timeout (20 min) | Mark workbranch failed, continue |
| Phase 1 resolution timeout in agent (10 min) | Agent exits failed, done marker written |
| wait_for timeout in agent (60 min) | Agent exits failed, done marker written |
| Rebase conflict | Attempt orchestrator resolution; if unresolvable, mark failed, continue |
| Push rejected (exit 3) | Retry once after 5 seconds; if still fails, mark failed, continue |
| Merge CLI failure (exit 2) | Mark failed, continue |
| Wave-transition no completion signal | Log warning, record in swarm state, continue |
| Halt condition (>50% blocked) | Halt, print rollback command, set status "halted" |
| All features in one wave fail | Halt immediately (bypass 50% calculation) |

### Contract consistency validation — exact checks

The validation in `/swarm` Step 5 applies these heuristic checks. If a check is ambiguous, log a warning rather than stopping.

1. Every capitalized name appearing in a model field type (e.g., `ownerId: string // references User.id`) must match a model name defined in the Models section.
2. Every path in File Structure must start with a valid directory character (no leading `/`, no `..` components).
3. No path in File Structure contradicts a path in Patterns. Contradiction means the same resource type is placed in two different directories by the two sections.
4. Every model name appearing in the API section (in descriptions or annotations) must exist in the Models section.

### Slug normalization — canonical algorithm

Used consistently across all components. Reference:

```bash
slugify() {
  echo "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/-/g' \
    | sed 's/-\+/-/g' \
    | sed 's/^-//;s/-$//' \
    | cut -c1-50
}
```

Plan slug: derived from plan filename. Strip the directory prefix, strip the `-plan.md` suffix, then apply `slugify`.

Workbranch slug: derived from the `# Workbranch: <Name>` heading. Strip the `# Workbranch: ` prefix, then apply `slugify`.

### Security considerations

1. **Slug sanitization:** Before using any slug in a file path or git tag name, verify it matches `^[a-z0-9-]+$`. The `slugify` function above enforces this. Never interpolate raw `$ARGUMENTS` into a path without slugification.

2. **Force-with-lease conflict with deny list:** The default permissions deny list in `.claude/settings.local.json` includes `Bash(git push --force*)`. The `--force-with-lease` flag is a distinct flag string but may match this pattern depending on how Claude Code evaluates the deny rule. The implementer must test this and choose one of the two resolution options documented in the `swarm-rebase-merge.sh` script header before shipping.

3. **Direct base branch commits by wave-transition:** The wave-transition agent commits auto-fixes, contract updates, and learnings directly to the base branch. This bypasses branch protection rules requiring PRs. Document this requirement: "The swarm requires direct push access to the base branch for the wave-transition agent's work. If your repository has branch protection enabled, the wave-transition auto-fix and commit steps will fail." The swarm continues (wave-transition failure is non-fatal) but contract and learnings updates will not persist.

4. **Contract backup:** `/plan` and `/import-plan` back up the existing `docs/project-contract.md` to `docs/project-contract.backup.md` before overwriting. Only one backup is kept — re-running `/plan` overwrites the backup too.

### Testing checklist

Before shipping, validate these scenarios end-to-end:

| Scenario | Expected result |
|---|---|
| `/init` on a fresh project | Creates settings.json, context template, `docs/plans/`, `docs/workbranches/`, `docs/reports/` |
| `/auto-dev "add login page"` with no contract file | Identical behavior to v1.0.0 |
| `/auto-dev "add login page"` with contract file present | Phase 1 reads contract, plan respects model shapes |
| `/auto-dev docs/workbranches/my-plan/auth.md` | Reads workbranch file, extracts sub-features, skips Phase 4.5 merge, writes done marker |
| `/plan` — new project (no src/) | Produces plan, contract, workbranch files after all three gates |
| `/plan` — existing project (has src/) | Produces plan and contract only; tells user to run /swarm for decomposition |
| `/import-plan` — file path | Reads file, extracts features, presents both drafts, requires explicit approval |
| `/import-plan` — inline text | Parses inline, same flow |
| `/swarm` — missing contract | Stops at Step 5, directs to /plan |
| `/swarm` — circular dependency in plan | Stops at Step 4, names the cycle |
| `/swarm` — happy path, two waves | Completes all 13 steps, produces report, all files present |
| `/swarm` — one feature fails | Dependents blocked, 50% check evaluated, unblocked features continue |
| `/swarm` — >50% blocked | Halts, prints rollback command, state written |
| `/swarm` — resume after halt | Resumes from correct wave, skips completed waves, failed features remain failed |
| `/swarm` — stale workbranch files | Re-decomposes when plan mtime > workbranch files mtime |
| Phase 1 sync — two agents claim same file | Orchestrator assigns to stronger-claim agent, other gets reassigned_files |
| Phase 1 sync — equally strong claim | Higher-priority agent proceeds first, lower-priority gets wait_for |
| Sequential merge — rebase conflict | Orchestrator resolves by type rule or marks failed; queue continues |
| Wave-transition — no completion signal | Warning logged, swarm continues |

### Backward compatibility summary

All changes are additive or conditionally guarded. No existing file is deleted. No existing interface is narrowed.

| File | Change type | Guard |
|---|---|---|
| `plugin.json` | Version bump + new fields | New fields are informational only |
| `commands/auto-dev.md` | Step 2 modified, Step 3 addendum | Workbranch detection requires `.md` extension + `# Workbranch:` heading |
| `skills/autonomous-feature-developer/SKILL.md` | New sections + new conditional phases | All new phases check `WORKBRANCH_FILE` or file existence |
| `references/phase-1-architecture.md` | New steps 3a, 3b, 3c, 5a | Steps skip if variable is empty or file does not exist |
| `scripts/setup.sh` | Third optional arg + one output line | Third arg is optional; callers with 2 args are unaffected |
| `commands/init.md` | New Step 3.5 + updated summary | `mkdir -p` is idempotent; summary is additive |