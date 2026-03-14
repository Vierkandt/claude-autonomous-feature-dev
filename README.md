# Autonomous Feature Developer & Swarm Orchestrator

A Claude Code plugin that builds features end-to-end and orchestrates parallel agent swarms for full-platform development.

## What it does

### Single feature — `/auto-dev`

Builds one feature from request to merged PR in a single run:

| Phase | What happens |
|---|---|
| **0 — Setup** | Create worktree + branch |
| **1 — Architecture** | Explore codebase, write + commit plan |
| **2 — Implementation** | Code the plan, verify build/tests/lint |
| **3 — Pull Request** | Push branch, open PR |
| **4 — Review & Fix** | Review → fix → verify loop (max 3 iterations) |
| **4.5 — Merge** | Squash/rebase/merge the PR |
| **5 — Cleanup** | Remove worktree |

### Full platform — `/plan` + `/swarm`

Brainstorm a platform, decompose it into features, and build them all in parallel:

1. `/plan` — interactive brainstorm producing a structured plan + project contract
2. `/swarm` — decomposes the plan into workbranches, dispatches parallel auto-dev agents in dependency-ordered waves, handles merging, runs post-wave reviews, produces a final report

```
/plan my-saas-platform
/swarm docs/plans/my-saas-platform-plan.md
```

### Other commands

| Command | Purpose |
|---|---|
| `/init` | Set up a project for auto-dev (permissions, context file, directories) |
| `/import-plan` | Parse a brainstorm export from Claude.ai into a structured plan + contract |

## Prerequisites

- **Git** with worktree support
- **`gh`** (GitHub) or **`glab`** (GitLab) CLI, authenticated
- **Claude Code** with agent teams support

## Installation

Add the repo as a marketplace, then install from it:

```
/plugin marketplace add Vierkandt/claude-autonomous-feature-dev
/plugin install develop-plugin@claude-autonomous-feature-dev
```

Or manage everything through the interactive UI:

```
/plugin
```

Go to **Marketplaces → Add**, paste `Vierkandt/claude-autonomous-feature-dev`, then install `develop-plugin` from the Discover tab.

## Setup

### 1. Initialize the project

```
/init
```

This creates `.claude/settings.local.json` with required permissions, copies the project context template, and sets up `docs/plans/`, `docs/workbranches/`, and `docs/reports/` directories.

### 2. Fill in the project context

Edit `docs/project-context.md` with your stack, build commands, coding conventions, and PR preferences. The plugin won't run without it.

## Usage

### Single feature

```
/auto-dev add a dark mode toggle to the settings page
```

Or natural language:
> "build this feature end-to-end: add CSV export to the reports page"

### Full platform

```
/plan
```

Answer the guided questions (platform, stack, deployment, features, conventions). The command produces:
- `docs/plans/<name>-plan.md` — structured plan
- `docs/project-contract.md` — shared conventions every agent follows

Then launch the swarm:

```
/swarm docs/plans/<name>-plan.md
```

Walk away. The swarm handles everything: decomposition, parallel agents, wave ordering, merge queue, post-wave reviews, integration review, and a final report at `docs/reports/`.

### Import from Claude.ai

If you brainstormed in the Claude app:

```
/import-plan docs/my-brainstorm.md
```

## Aborting & Recovery

For `/auto-dev`: tell Claude to clean up, or `git worktree list` and remove manually. Re-running is safe — setup is idempotent.

For `/swarm`: the swarm creates git tags at each wave boundary (`swarm/<slug>/pre-wave-N`). If halted, re-running `/swarm` with the same plan offers to resume from where it stopped. To roll back:

```bash
git revert --no-commit swarm/<slug>/pre-wave-N..HEAD
git commit -m "revert: roll back to pre-wave-N"
```
