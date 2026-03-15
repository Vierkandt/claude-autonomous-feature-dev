---
name: swarm
description: "Execute a swarm of parallel auto-dev agents against a plan file. Dispatches one agent per workbranch, manages wave ordering and dependency sequencing, handles the sequential merge queue, runs post-wave reviews, and produces a final report. Usage: /swarm <plan-file-path>. Requires docs/project-context.md and docs/project-contract.md. Run /plan or /import-plan first."
argument-hint: "<path to plan file, e.g. docs/plans/my-platform-plan.md>"
user-invocable: true
context: fork
agent: general-purpose
allowed-tools: Edit, Write, Glob, Grep, Read, Bash, Agent
---

# /swarm — Parallel Agent Swarm Execution Engine

## Step 1 — Verify environment

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

## Step 2 — Resolve plan file

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

## Step 3 — Check for existing swarm state

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

## Step 4 — Validate plan

Read `$PLAN_FILE`. Parse all features by scanning for `### Feature:` headings and extracting the Name, Dependencies, and Priority label lines that follow each heading.

Validations (stop on any failure, listing all errors found):
1. All feature names are unique (case-insensitive comparison)
2. All dependency references name features that exist in the plan (case-sensitive match against feature names)
3. No circular dependencies — perform topological sort; if it fails, report the cycle: "Circular dependency detected: FeatureA -> FeatureB -> FeatureA"

## Step 5 — Validate contract

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

### Exact consistency checks

1. Every capitalized name appearing in a model field type (e.g., `ownerId: string // references User.id`) must match a model name defined in the Models section.
2. Every path in File Structure must start with a valid directory character (no leading `/`, no `..` components).
3. No path in File Structure contradicts a path in Patterns. Contradiction means the same resource type is placed in two different directories by the two sections.
4. Every model name appearing in the API section (in descriptions or annotations) must exist in the Models section.

## Step 6 — Validate project context

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

## Step 7 — Staleness check and decomposition

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

If `PLAN_MTIME > WB_MTIME`: print "Plan was modified since last decomposition. Re-decomposing." Then invoke the decomposer agent.

If `WB_COUNT == 0`: invoke the decomposer agent.

If `WB_COUNT > 0` and plan is not newer: use existing workbranch files.

### Decomposer invocation

Invoke the `decomposer` agent via the Agent tool with these parameters:

```
tools: ["Read", "Write", "Glob", "Grep", "Bash"]
```

Prompt:

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

After decomposition (or using existing files), read all `*.md` files from `$WB_DIR` (excluding `swarm-state.json`) to build the workbranch list.

## Step 8 — Build dependency graph and print execution plan

Read all workbranch files. For each file, extract: the `# Workbranch: <Name>` heading, `## Dependencies` section, `## Priority` section, and `## Wave` section.

If Wave fields are missing, compute wave assignment via topological sort:
- Workbranches with `Dependencies: none` -> Wave 1
- Workbranches whose all dependencies are assigned to wave N or earlier -> Wave N+1

Sort workbranches within each wave by priority (high -> medium -> low -> alphabetical tiebreak).

Print:

```
Swarm execution plan — <Platform Name>

Wave 1 (2 workbranches, parallel):
  1. auth (high)
  2. config (medium)
  Merge order: auth -> config

Wave 2 (2 workbranches, parallel):
  1. dashboard (high) — depends on: auth
  2. billing (medium) — depends on: config
  Merge order: dashboard -> billing

Total: 4 workbranches across 2 waves.
```

Then print:

```
To monitor this swarm in real-time, open a second terminal and run:
  python -m dashboard <PLAN_SLUG> --base-dir <PROJECT_ROOT>

(Requires: pip install textual watchfiles)
```

## Step 9 — Initialize swarm state

If not resuming:

```bash
mkdir -p "docs/workbranches/${PLAN_SLUG}"
```

Write `docs/workbranches/${PLAN_SLUG}/swarm-state.json` with initial state:

```json
{
  "plan": "<relative path to plan file>",
  "plan_slug": "<PLAN_SLUG>",
  "contract_hash": "<sha1 of docs/project-contract.md content>",
  "started_at": "<ISO 8601 timestamp>",
  "updated_at": "<ISO 8601 timestamp>",
  "status": "running",
  "current_wave": 1,
  "waves_completed": [],
  "wave_results": {},
  "failed_features": [],
  "blocked_features": [],
  "tags": []
}
```

## Step 10 — Wave execution loop

For each wave N in order (starting from `current_wave` on resume):

### 10a. Skip completed waves

If `N` is in `waves_completed`, skip to the next wave.

### 10b. Tag pre-wave

```bash
git tag "swarm/${PLAN_SLUG}/pre-wave-${N}"
git push origin "swarm/${PLAN_SLUG}/pre-wave-${N}"
```

Append the tag to the state file's `tags` array. Write the updated state file.

### 10c. Collect workbranches for this wave

Read all workbranch files whose `## Wave` section equals N. Exclude any whose slug is in `failed_features` or `blocked_features`.

Print wave start banner:
```
═══════════════════════════════════════════
 Wave N starting — M workbranches
═══════════════════════════════════════════
```

### 10d. Dispatch auto-dev agents (parallel)

For each workbranch in the wave's set, invoke one Agent tool call. All agents are dispatched concurrently — do not wait for agent N to finish before dispatching agent N+1.

Update each workbranch file's `Status:` field from `pending` to `in-progress`.

For each dispatched agent, print:
```
  ⚙ <workbranch-name> — dispatched
```

Agent tool parameters:

```
tools: ["Edit", "Write", "Glob", "Grep", "Read", "NotebookEdit", "Bash"]
```

Prompt template (substitute angle-bracket placeholders with actual values):

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

### 10e. Phase 1 sync point

After dispatching all agents for the wave, poll for Phase 1 reports.

Poll every 60 seconds for all `<workbranch-slug>-phase1-report.json` files in `docs/workbranches/${PLAN_SLUG}/`.

Timeout: 20 minutes. Any workbranch that has not produced a report by then is marked failed: "Phase 1 report timeout."

As each phase1-report.json is detected, print:
```
  ✓ <workbranch-name> — Phase 1 complete, N files planned
  ✗ <workbranch-name> — Phase 1 timeout (20 min)
```

Once all reports are collected, build the conflict map:

```
file_path -> [workbranch_slug, ...]
```

For each file with more than one claimant, resolve:

1. Read both workbranch files. Read the contract's File Structure section.
2. Determine which workbranch has the stronger claim (whose feature description is more directly about this resource type — e.g., the auth workbranch has a stronger claim over `src/models/user.ts` than the dashboard workbranch).
3. The stronger-claim workbranch keeps the file. The other workbranch gets this file added to its `reassigned_files`.
4. If both workbranches have equally strong claims (both features genuinely need to write to the same file, e.g., both add exports to `src/types/index.ts`): sequence them. Higher-priority workbranch proceeds first. Lower-priority workbranch gets `wait_for` set to the higher-priority slug.

Write one resolution file per agent:

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

When all reports are in, print:
```
  Phase 1 sync: <N conflicts resolved | no conflicts>
```

### 10f. Wait for all agents to finish Phase 2–5

Poll every 60 seconds for `<workbranch-slug>-done.json` files in `docs/workbranches/${PLAN_SLUG}/`. If an agent has produced no done marker for more than 60 minutes, mark it as failed with reason "agent timeout (60 min)."

As each done marker is detected, print:
```
  ✓ <workbranch-name> — complete (PR #N, M review iterations)
```
or:
```
  ✗ <workbranch-name> — failed: <error summary>
```

### 10g. Sequential merge queue

After all done markers for a wave are present (or the 60-minute agent timeout is reached), run the sequential merge queue.

Sort workbranches by: priority (high -> medium -> low) then alphabetical.

For each workbranch in sorted order:

1. Read done marker. If status is `"failed"`: record "failed" in swarm state, skip.

2. Call:
```bash
bash "${SKILL_DIR}/scripts/swarm-rebase-merge.sh" \
  <worktree> <branch> <base-branch> \
  <pr-number> <pr-cli> <merge-strategy> <repo-root>
```

3. Exit 0 -> record "merged" in swarm state, continue to next.

4. Exit 1 (conflict) -> run conflict resolution (see below).

5. Exit 2 (CLI failure) -> record "failed" with error "merge CLI failure", continue.

6. Exit 3 (push rejected) -> wait 5 seconds, retry once. If retry fails -> record "failed" with error "push rejected after rebase", continue.

#### Orchestrator conflict resolution (exit 1)

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

Update the workbranch file's `Status:` field to `merged` or `failed` depending on the outcome.

Print merge queue progress for each workbranch:
```
  Merging: <name> — rebasing onto <base-branch>...
  ✓ <name> merged (PR #N)
  ✗ <name> — merge failed: <error summary>
  - <name> — skipped (failed during development)
```

### 10h. Tag post-wave

```bash
git tag "swarm/${PLAN_SLUG}/post-wave-${N}"
git push origin "swarm/${PLAN_SLUG}/post-wave-${N}"
```

Append the tag to the state file's `tags` array.

### 10i. Run wave-transition agent

Invoke the wave-transition agent via the Agent tool.

Agent tool parameters:

```
tools: ["Edit", "Write", "Read", "Glob", "Grep", "Bash"]
```

Prompt:

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

Wait for the agent to complete. Parse the `WAVE_TRANSITION_COMPLETE` block from its output. The lines immediately following it are parsed as key-value pairs:

```
WAVE_TRANSITION_COMPLETE
ISSUES_FOUND: N
ISSUES_AUTO_FIXED: N
MAJOR_WARNINGS: N
CONTRACT_UPDATES: N
LEARNINGS_ADDED: N
```

Store these values in the swarm state as annotations on `wave_results[N]` under the `_transition` key.

Print wave transition summary:
```
  Wave transition: N issues, N fixed, N contract updates, N learnings
───────────────────────────────────────────
```

If the completion block is not found, log: `WARN: wave-transition did not produce WAVE_TRANSITION_COMPLETE signal for wave N` and continue. The swarm does not halt on wave-transition failure.

### 10j. Update swarm state

Add N to `waves_completed`. Set `wave_results[N]` to a map of each workbranch slug to its status (from its done marker or merge queue result). Increment `current_wave` to N+1. Refresh `updated_at`. Write the state file.

### 10k. Halt check

Compute:
- `total_remaining` = count of workbranches not in any `waves_completed` wave's results
- `now_blocked` = count of workbranches transitively blocked by failures from this wave that were not already in `blocked_features`

Add `now_blocked` workbranch slugs to `blocked_features` in the state file.

**Special case:** if ALL workbranches in wave N failed, halt immediately without computing the percentage.

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

Update state: `status: "halted"`, `halt_reason: "<description>"`. Write state file. Stop execution.

Otherwise: log any failures and newly blocked features as warnings and continue to wave N+1.

Print halt check result:
```
  Halt check: N% remaining features blocked → continuing
  Halt check: N% remaining features blocked → HALTED
  Halt check: all workbranches in Wave N failed → HALTED
```

## Step 11 — Final integration review

After all waves complete, invoke the `integration-reviewer` skill via Agent tool.

Agent tool parameters:

```
tools: ["Edit", "Write", "Read", "Glob", "Grep", "Bash"]
```

Prompt:

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

Wait for it to complete. Extract `INTEGRATION_REVIEW_PR_URL=<url>` from its output.

Update state: set `integration_pr_url` to the extracted value.

## Step 12 — Write final report

Compose the report in this format:

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
- **Merge order:** <name> -> <name>
- **Phase 1 sync:** <"no ownership conflicts" or "N conflicts resolved: <description>">
- **Wave transition:** <N issues found>, <N auto-fixed>, <N warnings>, <N contract updates>, <N learnings>
- **Halt check:** <"N% blocked -> continue" or "N% blocked -> HALT">

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
- **Last error:** <1-2 sentence summary>
- **Rollback tag:** swarm/<slug>/pre-wave-<N>

### <Feature Name> (BLOCKED)
- **Blocked by:** <failed feature name>
- **Transitively blocked by:** <root failed feature name, if chain is longer than one step>
```

Determine the output path:

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

## Step 13 — Generate or update README

Check if `README.md` exists at the project root.

**If README.md does NOT exist:** Generate one from scratch using:
- Platform name and overview from the plan document
- Stack info from `docs/project-context.md`
- Features list from the plan (mark any that failed/blocked with their status)
- Setup instructions derived from the build/install commands in the context file
- API overview from `docs/project-contract.md` (endpoints, auth mechanism, error format)

**If README.md DOES exist:** Read it and apply additions:
- Add or update a Features section with the newly built features
- Add any new setup steps required by new features
- Update API documentation if new endpoints were added

Write the README and commit:

```bash
git add -- README.md
git commit -m "docs: auto-generate README after swarm run"
```

The README should be practical and user-facing — not a dump of internal plan/contract details. It should answer: what is this, how do I set it up, how do I run it, what can it do.

If README generation or the commit fails, log a warning and continue to Step 14. Do not mark the swarm as failed — README generation is best-effort.

## Step 14 — Print terminal summary

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

## Input/output contract

- Input: `$ARGUMENTS` — path to plan file (required)
- Reads: plan file, `docs/project-context.md`, `docs/project-contract.md`
- Writes: `docs/workbranches/${PLAN_SLUG}/swarm-state.json`, `docs/project-contract.md` (via wave-transition agent), `docs/wave-learnings.md` (via wave-transition agent), `docs/reports/*.md`, `README.md`
- Git side effects: creates and pushes git tags, creates and merges PRs (via auto-dev agents), commits report and state file, commits README

## Error handling

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
