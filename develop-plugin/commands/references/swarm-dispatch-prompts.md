# Swarm Dispatch Prompt Templates

## Decomposer Prompt Template

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
Write workbranch files to: ${PROJECT_ROOT}/docs/workbranches/<PLAN_SLUG>/
Print the decomposition summary when done.
```

## Auto-dev Dispatch Prompt Template

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
         Read ${PROJECT_ROOT}/docs/project-contract.md (required).
         Read ${PROJECT_ROOT}/docs/wave-learnings.md if it exists.
         After committing your plan, perform the Phase 1 sync point protocol.
         See references/phase-1-architecture.md Step 5a.
Phase 2: Implement according to the plan. Follow the contract for all shared concerns.
Phase 3: Create the PR.
Phase 4: Run the review and fix loop.
Phase 4.5: SKIP. Do not merge the PR. /swarm handles merging.
Phase 5.5: Write the done marker file. See SKILL.md Phase 5.5.
Phase 5: Run cleanup.
```

## Wave-transition Prompt Template

```
You are the wave-transition agent. Run a single-pass post-wave review for Wave <N>.

## Parameters
WAVE_NUMBER=<N>
PLAN_SLUG=<PLAN_SLUG>
PRE_WAVE_TAG=swarm/<PLAN_SLUG>/pre-wave-<N>
POST_WAVE_TAG=swarm/<PLAN_SLUG>/post-wave-<N>
CONTRACT_FILE=${PROJECT_ROOT}/docs/project-contract.md
LEARNINGS_FILE=${PROJECT_ROOT}/docs/wave-learnings.md
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

## Integration-reviewer Prompt Template

```
You are the integration reviewer. Run a final review of the fully merged codebase.

## Parameters
PLAN_FILE=<PLAN_FILE_PATH>
CONTRACT_FILE=${PROJECT_ROOT}/docs/project-contract.md
LEARNINGS_FILE=${PROJECT_ROOT}/docs/wave-learnings.md
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
