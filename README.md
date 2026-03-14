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

Clone the repo directly into your Claude plugins directory:

**macOS / Linux:**
```bash
git clone https://github.com/Vierkandt/claude-autonomous-feature-dev \
  ~/.claude/plugins/develop-plugin
```

**Windows (Git Bash):**
```bash
git clone https://github.com/Vierkandt/claude-autonomous-feature-dev \
  ~/.claude/plugins/develop-plugin
```

No `claude plugin install` needed — Claude Code discovers plugins placed in the plugins directory automatically on next startup.

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

Copy the template into your project and fill it in:

```bash
cp ~/.claude/plugins/cache/claude-autonomous-feature-dev/assets/project-context.template.md docs/project-context.md
```

The context file tells the skill your stack, build commands, coding conventions, and PR preferences. The skill won't run without it.

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

If the pipeline is interrupted, clean up the worktree manually:

```bash
bash ~/.claude/plugins/cache/claude-autonomous-feature-dev/scripts/merge-cleanup.sh cleanup <worktree-path>
```

To list active worktrees: `git worktree list`

Re-running `/auto-dev` with the same feature description is safe — setup is idempotent and will reuse the existing worktree and branch.
