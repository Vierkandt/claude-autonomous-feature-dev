# Autonomous Feature Developer

A Claude Code plugin that builds features end-to-end — architecture, implementation, PR, review, and merge — without hand-holding.

## Pipeline

| Phase | What happens |
|---|---|
| **0 — Setup** | Create worktree + branch |
| **1 — Architecture** | Explore codebase, write + commit plan |
| **2 — Implementation** | Code the plan, verify build/tests/lint |
| **3 — Pull Request** | Push branch, open PR |
| **4 — Review & Fix** | Review → fix → verify loop (max 3 iterations) |
| **4.5 — Merge** | Squash/rebase/merge the PR |
| **5 — Cleanup** | Remove worktree |

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

### 1. Configure permissions

Add to your project's `.claude/settings.local.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "permissions": {
    "allow": [
      "Edit", "Write", "Glob", "Grep", "Read", "NotebookEdit", "Bash(*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git reset --hard*)",
      "Bash(git push --force*)",
      "Bash(git clean *)"
    ]
  }
}
```

### 2. Add a project context file

Copy the template into your project and fill it in. The template is bundled with the plugin — after installation, the skill will reference it automatically via `${CLAUDE_SKILL_DIR}/assets/project-context.template.md`. You can also copy it manually:

```
/auto-dev set up project context
```

Or ask Claude to copy the template for you. The context file tells the skill your stack, build commands, coding conventions, and PR preferences. The skill won't run without it.

## Usage

### Slash command

```
/auto-dev add a dark mode toggle to the settings page
```

### Natural language (skill auto-triggers)

> "build this feature end-to-end: add CSV export to the reports page"
> "ship this"
> "implement this autonomously"

## Aborting & Recovery

If the pipeline is interrupted, tell Claude to clean up:

> "clean up the worktree from the last auto-dev run"

Or list active worktrees with `git worktree list` and remove manually.

Re-running `/auto-dev` with the same feature description is safe — setup is idempotent and will reuse the existing worktree and branch.
