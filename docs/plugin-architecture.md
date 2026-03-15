# Develop Plugin — Architecture & Process Logic

**Plugin:** develop-plugin v2.0.0
**Author:** Vierkandt
**Generated:** 2026-03-15

---

## Table of Contents

1. [Plugin Structure](#1-plugin-structure)
2. [Component Inventory](#2-component-inventory)
3. [Process Logic: /init](#3-process-logic-init)
4. [Process Logic: /auto-dev](#4-process-logic-auto-dev)
5. [Process Logic: /plan](#5-process-logic-plan)
6. [Process Logic: /import-plan](#6-process-logic-import-plan)
7. [Process Logic: /swarm](#7-process-logic-swarm)
8. [Process Logic: /dashboard](#8-process-logic-dashboard)
9. [Agent Specifications](#9-agent-specifications)
10. [Skill Pipelines](#10-skill-pipelines)
11. [Data Flow & State Files](#11-data-flow--state-files)
12. [Safety Guardrails](#12-safety-guardrails)

---

## 1. Plugin Structure

```
develop-plugin/
├── .claude-plugin/
│   └── plugin.json                          # Manifest (v2.0.0)
├── commands/
│   ├── auto-dev.md                          # Single feature builder
│   ├── dashboard.md                         # Live TUI monitor
│   ├── import-plan.md                       # Brainstorm → plan parser
│   ├── init.md                              # Project initializer
│   ├── plan.md                              # Interactive planner
│   └── swarm.md                             # Parallel orchestration engine
├── agents/
│   ├── decomposer.md                        # Plan → workbranch decomposer
│   ├── swarm-orchestrator.md                # Swarm operations intelligence
│   └── wave-transition.md                   # Post-wave review agent
├── skills/
│   ├── autonomous-feature-developer/
│   │   ├── SKILL.md                         # 5-phase feature pipeline
│   │   ├── references/
│   │   │   ├── phase-1-architecture.md
│   │   │   ├── phase-2-implementation.md
│   │   │   ├── phase-3-pull-request.md
│   │   │   ├── phase-4-review-fix.md
│   │   │   ├── review-rubric.md
│   │   │   ├── bug-report-protocol.md
│   │   │   └── progress-protocol.md
│   │   ├── assets/
│   │   │   ├── project-context.template.md
│   │   │   └── project-contract.template.md
│   │   └── scripts/
│   │       ├── setup.sh
│   │       ├── verify.sh
│   │       ├── create-pr.sh
│   │       ├── merge-cleanup.sh
│   │       └── swarm-rebase-merge.sh
│   └── integration-reviewer/
│       └── SKILL.md                         # Post-swarm review + cleanup PR
└── scripts/
    └── dashboard/                           # Textual TUI application
        ├── __init__.py
        ├── __main__.py
        ├── app.py
        ├── models.py
        ├── state.py
        ├── requirements.txt
        ├── css/dashboard.tcss
        └── widgets/
            ├── __init__.py
            ├── header.py
            ├── wave_panel.py
            ├── merge_queue.py
            └── detail_panel.py
```

---

## 2. Component Inventory

| Type | Count | Components |
|------|-------|------------|
| Commands | 6 | `/init`, `/auto-dev`, `/plan`, `/import-plan`, `/swarm`, `/dashboard` |
| Agents | 3 | decomposer, swarm-orchestrator, wave-transition |
| Skills | 2 | autonomous-feature-developer, integration-reviewer |
| Shell scripts | 5 | setup.sh, verify.sh, create-pr.sh, merge-cleanup.sh, swarm-rebase-merge.sh |
| Dashboard widgets | 4 | header, wave_panel, merge_queue, detail_panel |
| Reference docs | 7 | phase-1 through phase-4, review-rubric, bug-report, progress protocol |
| Asset templates | 2 | project-context, project-contract |

---

## 3. Process Logic: /init

**Purpose:** One-time project setup for autonomous development.

```
/init
  │
  ├─ 1. Create .claude/settings.local.json
  │     ├─ Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
  │     ├─ Allow: Bash(*), Edit, Write, Read, Glob, Grep, NotebookEdit
  │     └─ Deny: rm -rf, git reset --hard, git push --force, git clean
  │
  ├─ 2. Copy project-context template
  │     └─ assets/project-context.template.md → docs/project-context.md
  │
  ├─ 3. Create directory structure
  │     ├─ docs/plans/
  │     ├─ docs/workbranches/
  │     └─ docs/reports/
  │
  └─ 4. Print next steps
        └─ "Edit docs/project-context.md with your stack, commands, conventions"
```

**Inputs:** None required
**Outputs:** `.claude/settings.local.json`, `docs/project-context.md`, directory structure

---

## 4. Process Logic: /auto-dev

**Purpose:** Build one feature from description to merged PR.

```
/auto-dev <feature description>
  │
  ├─ 1. Verify environment
  │     ├─ Check CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
  │     └─ Stop if not set (print setup instructions)
  │
  ├─ 2. Invoke autonomous-feature-developer skill
  │     │
  │     ├─ Phase 0 — Setup
  │     │   ├─ Run setup.sh: create worktree + branch
  │     │   ├─ Derive SLUG from feature description
  │     │   └─ Capture: WORKTREE, BRANCH, PLAN_FILE, CONTEXT_FILE
  │     │
  │     ├─ Phase 1 — Architecture
  │     │   ├─ Read project-context.md (extract BUILD_CMD, TEST_CMD, etc.)
  │     │   ├─ Read project-contract.md if exists
  │     │   ├─ Explore codebase (structure, patterns, conventions)
  │     │   ├─ Write implementation plan to PLAN_FILE
  │     │   └─ Commit plan
  │     │
  │     ├─ Phase 2 — Implementation
  │     │   ├─ Code the plan (follow contract if exists)
  │     │   ├─ Run verify.sh (build + test + lint)
  │     │   ├─ If verify fails: fix → retry (max 5 attempts)
  │     │   └─ Commit implementation
  │     │
  │     ├─ Phase 3 — Pull Request
  │     │   ├─ Push branch to remote
  │     │   ├─ Run create-pr.sh (gh pr create / glab mr create)
  │     │   └─ Capture PR_URL, PR_NUMBER
  │     │
  │     ├─ Phase 4 — Review & Fix
  │     │   ├─ Self-review using review-rubric.md
  │     │   ├─ If issues found: fix → verify → re-review
  │     │   ├─ Max 3 iterations
  │     │   └─ Spawn parallel fix agents for multi-domain issues
  │     │
  │     ├─ Phase 4.5 — Merge
  │     │   ├─ Run merge-cleanup.sh merge
  │     │   └─ Squash/rebase/merge per MERGE_STRATEGY
  │     │
  │     └─ Phase 5 — Cleanup
  │         └─ Run merge-cleanup.sh cleanup (remove worktree)
  │
  └─ Done: Feature built, PR merged, worktree removed
```

**Inputs:** Feature description (natural language)
**Outputs:** Merged PR, clean worktree

---

## 5. Process Logic: /plan

**Purpose:** Interactive brainstorm producing a structured plan + project contract.

```
/plan [topic]
  │
  ├─ Phase A — Feature Brainstorming
  │   ├─ Ask guided questions (platform, stack, deployment, features)
  │   ├─ User answers interactively
  │   ├─ Extract features, priorities, dependencies
  │   └─ Draft: docs/plans/<slug>-plan.md
  │
  ├─ Phase B — Convention Negotiation
  │   ├─ Propose conventions (file structure, naming, patterns)
  │   ├─ User approves/modifies each convention
  │   ├─ If docs/project-contract.md exists:
  │   │   └─ Back up with timestamp before overwriting
  │   └─ Write: docs/project-contract.md
  │
  └─ Phase C — Decomposition (new projects only)
      ├─ If IS_EXISTING_PROJECT: skip
      ├─ Invoke decomposer agent
      │   ├─ Split features into workbranches
      │   ├─ Assign wave numbers (topological sort)
      │   ├─ Define sub-features per workbranch
      │   └─ Assign file ownership
      └─ Write: docs/workbranches/<slug>/*.md
```

**Inputs:** Optional starting topic
**Outputs:** Plan file, project contract, workbranch files (new projects)

---

## 6. Process Logic: /import-plan

**Purpose:** Parse an external brainstorm document into a structured plan.

```
/import-plan <file-path or pasted text>
  │
  ├─ 1. Read input (file or inline text)
  │
  ├─ 2. Parse features via heuristics
  │     ├─ Extract numbered lists, headings, bullet points
  │     ├─ Identify dependencies (mentions of other features)
  │     └─ Assign priorities (explicit or inferred)
  │
  ├─ 3. Draft plan file
  │     └─ Present for user confirmation before writing
  │
  ├─ 4. Negotiate conventions → project contract
  │     ├─ If existing contract: back up with timestamp
  │     └─ Write docs/project-contract.md
  │
  └─ 5. Decompose (new projects only)
        └─ Same as /plan Phase C
```

**Inputs:** Brainstorm document (file path or pasted text)
**Outputs:** Plan file, project contract, workbranch files

---

## 7. Process Logic: /swarm

**Purpose:** Orchestrate parallel agent swarm for multi-feature builds.

This is the most complex command. The full pipeline has 13 steps with a nested wave loop.

### Steps 1-9: Setup & Validation

```
/swarm <plan-file-path>
  │
  ├─ Step 1: Verify environment
  │   └─ Check CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
  │
  ├─ Step 2: Resolve plan file
  │   ├─ Set PROJECT_ROOT = git rev-parse --show-toplevel
  │   ├─ Set PLAN_FILE = ${PROJECT_ROOT}/${ARGUMENTS}
  │   ├─ Verify file exists
  │   └─ Derive PLAN_SLUG from filename
  │
  ├─ Step 3: Check for existing swarm state
  │   ├─ Read swarm-state.json if exists
  │   ├─ If halted/in-progress: offer resume or fresh start
  │   └─ Resume: load state, jump to Step 10 at current_wave
  │
  ├─ Step 4: Parse and validate plan
  │   ├─ Check for duplicate names, bad dependency refs
  │   └─ Stop on circular dependencies
  │
  ├─ Step 5: Validate project contract
  │   ├─ Verify docs/project-contract.md exists
  │   └─ Cross-check against plan (all features covered)
  │
  ├─ Step 6: Validate project context
  │   ├─ Verify docs/project-context.md exists
  │   └─ Ensure BUILD_CMD is defined
  │
  ├─ Step 7: Check workbranch staleness + decompose
  │   ├─ If workbranch files older than plan: re-decompose
  │   ├─ Invoke decomposer agent if needed
  │   └─ Read all *.md files from workbranch directory
  │
  ├─ Step 8: Build dependency graph
  │   ├─ Extract dependencies, priorities, wave assignments
  │   └─ Print execution plan (wave → features table)
  │
  └─ Step 9: Initialize state file
      └─ Write swarm-state.json (status: running, current_wave: 1)
```

### Step 10: Wave Execution Loop

This is the core orchestration loop, running once per wave.

```
Step 10: FOR EACH WAVE N
  │
  ├─ 10a. Print wave banner
  │
  ├─ 10b. Tag pre-wave
  │   └─ git tag swarm/<PLAN_SLUG>/pre-wave-N
  │
  ├─ 10c. Pre-wave worktree checks
  │   ├─ Verify orchestrator is NOT inside a worktree
  │   ├─ git worktree prune
  │   └─ Remove rogue .claude/settings.local.json in worktrees
  │
  ├─ 10d. Dispatch auto-dev agents (PARALLEL)
  │   ├─ For each workbranch in wave:
  │   │   ├─ Update workbranch status: pending → in-progress
  │   │   └─ Agent(isolation: "worktree", run_in_background: true)
  │   │       ├─ Reads workbranch file
  │   │       ├─ Invokes autonomous-feature-developer skill
  │   │       └─ Writes done marker on completion
  │   └─ All agents dispatched concurrently
  │
  ├─ 10e. Phase 1 sync point
  │   ├─ Poll every 60s for *-phase1-report.json files
  │   ├─ Timeout: 20 minutes → mark failed
  │   ├─ When all reports in:
  │   │   ├─ Detect file conflicts between agents
  │   │   ├─ Write *-phase1-resolution.json per agent
  │   │   └─ Agents read resolution and continue to Phase 2
  │   └─ Print sync summary
  │
  ├─ 10f. Poll for done markers
  │   ├─ Poll every 60s for *-done.json files
  │   ├─ Agent timeout: 60 minutes → mark failed
  │   ├─ Print status as each agent completes
  │   └─ Post-agent cleanup (failed worktrees + branches)
  │
  ├─ 10g. Sequential merge queue
  │   ├─ Order: by priority (high → medium → low), then alphabetical
  │   ├─ For each completed workbranch:
  │   │   ├─ Run swarm-rebase-merge.sh
  │   │   │   ├─ Fetch latest base branch
  │   │   │   ├─ Rebase feature branch onto base
  │   │   │   ├─ If conflict: attempt resolution, or mark failed
  │   │   │   └─ Merge PR (gh pr merge --squash/--rebase)
  │   │   └─ Print merge result (✓ merged / ✗ failed)
  │   └─ Skip failed workbranches
  │
  ├─ 10h. Tag post-wave + cleanup
  │   ├─ git tag swarm/<PLAN_SLUG>/post-wave-N
  │   ├─ git worktree prune
  │   └─ Check for orphaned worktree directories
  │
  ├─ 10i. Wave-transition agent
  │   ├─ Invoke wave-transition agent
  │   │   ├─ Micro-review: contract compliance of merged code
  │   │   ├─ Contract updates: additive/corrective only
  │   │   └─ Wave learnings: append to docs/wave-learnings.md
  │   └─ Parse completion signal for metrics
  │
  ├─ 10j. Update state file
  │   ├─ Record wave results (merged/failed per workbranch)
  │   ├─ Add wave to waves_completed list
  │   └─ Increment current_wave
  │
  └─ 10k. Halt check
      ├─ If >50% of remaining features blocked/failed → HALT
      ├─ If all features in this wave failed → HALT immediately
      └─ Otherwise: continue to next wave
```

### Steps 11-13: Finalization

```
  ├─ Step 11: Integration review
  │   ├─ Invoke integration-reviewer skill
  │   │   ├─ Completeness check (every feature has code)
  │   │   ├─ Cross-wave consistency
  │   │   ├─ Contract compliance
  │   │   ├─ Duplication scan
  │   │   ├─ Dead code scan
  │   │   └─ Create cleanup PR (or "none" if clean)
  │   └─ Record integration PR URL in state
  │
  ├─ Step 12: Generate report
  │   ├─ Write docs/reports/<PLAN_SLUG>-swarm-report.md
  │   ├─ Include: per-wave results, merged PRs, failures, metrics
  │   └─ Commit report + state file
  │
  ├─ Step 13: Generate/update README
  │   ├─ Best-effort: read codebase, write README.md
  │   └─ Commit README (if generated)
  │
  └─ Step 14: Print terminal summary
      ├─ Status, waves completed, features merged/failed
      ├─ Total elapsed time
      ├─ Report path, integration PR URL
      └─ Rollback command (if applicable)
```

---

## 8. Process Logic: /dashboard

**Purpose:** Real-time TUI for monitoring a running swarm.

```
/dashboard [plan-slug]
  │
  ├─ 1. Resolve plan slug
  │   ├─ If provided: use it
  │   ├─ If one plan exists in docs/workbranches/: auto-detect
  │   └─ If multiple: list and ask user to choose
  │
  ├─ 2. Check Python + dependencies
  │   ├─ Verify python3 available
  │   ├─ Check textual, watchfiles, rich are installed
  │   └─ If missing: pip install from requirements.txt
  │
  ├─ 3. Launch dashboard
  │   ├─ Set PYTHONPATH
  │   └─ python -m dashboard <plan-slug> --base-dir $(pwd)
  │
  └─ 4. Dashboard runtime
      ├─ Read state: SwarmStateReader parses all JSON/MD files
      ├─ Build UI: Header + WavePanels + DetailPanel + MergeQueueBar
      ├─ File watcher: watchfiles on docs/workbranches/<slug>/
      │   └─ Fallback: 5-second polling if watchfiles unavailable
      ├─ On state change: rebuild widgets with new data
      └─ Keybindings:
          ├─ q — quit
          ├─ r — force refresh
          ├─ d — toggle detail panel
          ├─ ↑/↓ — navigate workbranches
          ├─ Enter — open PR in browser
          ├─ l — show wave learnings
          ├─ c — show contract
          └─ e — show error detail
```

**State files consumed:**
- `swarm-state.json` — overall status, current wave, failed/blocked features
- `*-done.json` — per-workbranch completion markers (PR URL, status, errors)
- `*-phase1-report.json` — Phase 1 architecture reports
- `*-phase1-resolution.json` — Phase 1 conflict resolutions
- `*-progress.json` — agent heartbeats (current action, sub-feature progress)
- `*-bug-report.md` — structured error diagnostics
- `*.md` (workbranch files) — feature specs, wave/priority/dependency metadata

---

## 9. Agent Specifications

### Decomposer Agent

| Property | Value |
|----------|-------|
| **Trigger** | Called by `/plan` (Phase C) and `/swarm` (Step 7) |
| **Input** | Plan, contract, context, plan slug, IS_EXISTING_PROJECT |
| **Output** | Workbranch files in `docs/workbranches/<plan-slug>/` |
| **Codebase-aware** | Yes (for existing projects: explores before decomposing) |
| **Split criteria** | >8 sub-features, independent merge points, distinct file domains |
| **Wave assignment** | Topological sort on dependencies |

### Swarm Orchestrator Agent

| Property | Value |
|----------|-------|
| **Trigger** | Natural language ("swarm this", "build the whole platform") |
| **Role** | Operations intelligence — NOT the executor |
| **Pre-launch** | Find plans, validate readiness, advise on concurrency |
| **Runtime** | Progress reporting, failure diagnosis, halt explanation |
| **Post-run** | Grouped failure analysis, contract deviations, bulk fix suggestions |
| **Hard constraint** | Does NOT generate plans — directs to `/plan` or `/import-plan` |

### Wave-Transition Agent

| Property | Value |
|----------|-------|
| **Trigger** | Called by `/swarm` (Step 10i) after each wave's merge queue |
| **Input** | Pre/post wave tags, merged workbranches, contract, learnings |
| **Output** | Auto-fixes PR, contract updates, wave learnings |
| **Constraint** | Contract updates are additive/corrective only (never remove) |
| **Signal** | Prints `WAVE_TRANSITION_COMPLETE` block with metrics |

---

## 10. Skill Pipelines

### Autonomous Feature Developer

```
Phase 0: Setup
  └─ setup.sh → SLUG, BRANCH, WORKTREE, PLAN_FILE, CONTEXT_FILE

Phase 1: Architecture
  ├─ Read context + contract
  ├─ Explore codebase
  ├─ Write plan → commit
  └─ [Swarm only] Write phase1-report.json → wait for resolution

Phase 2: Implementation
  ├─ Code the plan
  ├─ verify.sh (build + test + lint)
  └─ Retry loop (max 5)

Phase 3: Pull Request
  ├─ create-pr.sh → PR_URL, PR_NUMBER
  └─ [Swarm only] Write progress heartbeat

Phase 4: Review & Fix
  ├─ Self-review (review-rubric.md)
  ├─ Fix → verify → re-review (max 3 iterations)
  └─ Spawn parallel fix agents for multi-domain issues

Phase 4.5: Merge (standalone only — swarm skips)
  └─ merge-cleanup.sh merge

Phase 5: Cleanup
  └─ merge-cleanup.sh cleanup

Phase 5.5: Done Marker (swarm only)
  └─ Write *-done.json with status, PR info, errors

[On error]: Write bug report before done marker
[During execution]: Write progress heartbeats (swarm only)
```

### Integration Reviewer

```
Phase 1: Orientation
  └─ Read plan, contract, learnings, git log

Phase 2: Completeness
  └─ Every non-failed feature has code? → list gaps

Phase 3: Cross-wave consistency
  └─ Features from different waves interact correctly?

Phase 4: Contract compliance
  └─ Models, file structure, patterns match final contract?

Phase 5: Duplication scan
  └─ Duplicate exports, redundant utilities across features?

Phase 6: Dead code scan
  └─ TODOs, FIXMEs, stubs, commented blocks?

Phase 7: Create cleanup PR
  └─ Apply auto-fixes → gh pr create (or "none" if clean)
```

---

## 11. Data Flow & State Files

### File Flow Through a Swarm Run

```
docs/project-context.md ─────────────────────────────────────────────┐
docs/project-contract.md ────────────────────────────────────────────┤
docs/plans/<slug>-plan.md ───────────────────────────────────────────┤
                                                                     │
  ┌──────────────────────────────────────────────────────────────────┘
  │
  ▼
docs/workbranches/<slug>/
  ├── <feature>.md                    ← workbranch specs (input)
  ├── swarm-state.json                ← orchestrator state (read/write)
  ├── <feature>-phase1-report.json    ← agent → orchestrator
  ├── <feature>-phase1-resolution.json← orchestrator → agent
  ├── <feature>-progress.json         ← agent → dashboard
  ├── <feature>-done.json             ← agent → orchestrator
  └── <feature>-bug-report.md         ← agent → dashboard/human

docs/wave-learnings.md               ← wave-transition agent (append)
docs/reports/<slug>-swarm-report.md   ← orchestrator (final)
```

### State File: swarm-state.json

```json
{
  "status": "running | halted | completed",
  "started_at": "ISO 8601",
  "current_wave": 2,
  "plan": "docs/plans/<slug>-plan.md",
  "failed_features": ["feature-a"],
  "blocked_features": [],
  "waves_completed": [1],
  "wave_results": {
    "1": {
      "feature-x": "merged",
      "feature-y": "failed",
      "_transition": {
        "ISSUES_FOUND": 3,
        "ISSUES_AUTO_FIXED": 2,
        "MAJOR_WARNINGS": 0,
        "CONTRACT_UPDATES": 1,
        "LEARNINGS_ADDED": 2
      }
    }
  },
  "tags": ["swarm/<slug>/pre-wave-1", "swarm/<slug>/post-wave-1"],
  "halt_reason": "",
  "integration_pr_url": "",
  "report_path": ""
}
```

### Done Marker: *-done.json

```json
{
  "workbranch": "feature-slug",
  "status": "merged | failed",
  "pr_number": "42",
  "pr_url": "https://github.com/...",
  "review_iterations": 2,
  "error": "",
  "reason": "",
  "contract_deviations": [],
  "bug_report": ""
}
```

---

## 12. Safety Guardrails

### Permission Model

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| Allow list | `Bash(*)`, Edit, Write, Read, Glob, Grep, NotebookEdit | All agents |
| Deny list | `rm -rf`, `git reset --hard`, `git push --force`, `git clean` | All agents |
| Worktree isolation | `isolation: "worktree"` on Agent tool | Feature agents |
| Instruction-based | Prompt constraints (no git worktree add, no settings writes) | Feature agents |
| Contract | Project contract defines file ownership and conventions | All agents |

### Worktree Guardrails

| Check | When | Action |
|-------|------|--------|
| Orchestrator not inside worktree | Pre-wave (10c) | Abort if violated |
| Rogue settings files | Pre-wave (10c) | Auto-remove |
| Stale worktrees | Pre-wave (10c) + post-wave (10h) | `git worktree prune` |
| Failed agent cleanup | Post-agent (10f) | Force-remove worktree + delete branch |
| Orphaned directories | Post-wave (10h) | Warn operator |
| Agent constraints | Agent prompt injection | Block: git worktree add, nested worktrees, settings writes |

### Halt Conditions

| Condition | Trigger | Action |
|-----------|---------|--------|
| >50% blocked/failed | Step 10k | Halt, print rollback command |
| All features in wave fail | Step 10k | Halt immediately |
| Agent timeout (60 min) | Step 10f | Mark failed, continue |
| Phase 1 timeout (20 min) | Step 10e | Mark failed, continue |

### Recovery

- **Resume:** Re-run `/swarm` with same plan → offers to resume from last wave
- **Rollback:** `git revert --no-commit swarm/<slug>/pre-wave-N..HEAD`
- **Tags:** Pre/post-wave tags provide clean rollback points
