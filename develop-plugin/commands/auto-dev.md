---
name: auto-dev
description: Autonomously build a feature end-to-end — architecture, implementation, PR, review, and merge — without human hand-holding. Usage: /auto-dev <feature description>. Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 and Bash(*) in permissions.
argument-hint: "<feature description>"
user-invocable: true
context: fork
agent: general-purpose
allowed-tools: Edit, Write, Glob, Grep, Read, NotebookEdit, Bash
---

## Step 1 — Verify required configuration

Run this before doing anything else:

```bash
echo "AGENT_TEAMS=${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-NOT_SET}"
```

**If the output is `AGENT_TEAMS=NOT_SET`** — stop immediately, display the message below, and do nothing further:

```
/auto-dev requires agent teams and elevated permissions.

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

## Step 3 — Run the pipeline

You are an autonomous feature developer. Build the feature end-to-end without pausing for user input.

Invoke the `autonomous-feature-developer` skill and follow it exactly. Execute all phases in order:

1. Phase 0 — Setup (worktree + branch)
2. Phase 1 — Architecture (write + commit plan)
3. Phase 2 — Implementation (code + verify)
4. Phase 3 — Pull Request (push + open PR)
5. Phase 4 — Review & Fix loop (max 3 iterations, spawn parallel fix agents per domain in bypassPermissions mode)
6. Phase 4.5 — Merge (clean up plan file, merge PR)
7. Phase 5 — Cleanup (remove worktree)

Report final status when done using the Done table from the skill.
