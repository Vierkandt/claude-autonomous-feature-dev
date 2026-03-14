---
name: auto-dev
description: Autonomously build a feature end-to-end — architecture, implementation, PR, review, and merge — without human hand-holding. Usage: /auto-dev <feature description>. Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 and Bash(*) in permissions.
argument-hint: "<feature description>"
---

## Step 1 — Verify required configuration

Run this before doing anything else:

```bash
echo "AGENT_TEAMS=${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-NOT_SET}"
```

**If the output is `AGENT_TEAMS=NOT_SET`** — stop immediately, display the message below, and do nothing further:

```
❌ /auto-dev requires agent teams and elevated permissions.

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

Then re-run: /auto-dev <feature description>
```

**If the output is `AGENT_TEAMS=1`** — proceed to Step 2.

---

## Step 2 — Get the feature request

The feature request is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, ask the user: "What feature would you like to build?"

---

## Step 3 — Dispatch autonomous agent

Spawn a single Agent in `bypassPermissions` mode to run the complete pipeline.
The agent must not pause for confirmation between phases.

Agent prompt:

```
You are an autonomous feature developer. Your job is to build the following feature
end-to-end without pausing for user input:

FEATURE: $ARGUMENTS

Follow the autonomous-feature-developer skill exactly. Execute all phases in order:
  Phase 0 — Setup (worktree + branch)
  Phase 1 — Architecture (write + commit plan)
  Phase 2 — Implementation (code + verify)
  Phase 3 — Pull Request (push + open PR)
  Phase 4 — Review & Fix loop (max 3 iterations, spawn parallel fix agents per domain)
  Phase 4.5 — Merge (clean up plan file, merge PR)
  Phase 5 — Cleanup (remove worktree)

Run the full pipeline autonomously. When Phase 4 calls for parallel fix agents,
spawn them in bypassPermissions mode. Report final status when done.
```
