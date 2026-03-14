---
name: init
description: Set up the current project for autonomous feature development. Creates .claude/settings.local.json with required permissions and copies the project context template. Run this once per project before using /auto-dev.
argument-hint: "[context-file-path]"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

## Step 1 — Check current state

Check what already exists:

```bash
echo "SETTINGS_EXISTS=$([ -f .claude/settings.local.json ] && echo yes || echo no)"
echo "CONTEXT_EXISTS=$([ -f docs/project-context.md ] && echo yes || echo no)"
```

Also check if the user specified an alternate context file path via `$ARGUMENTS`. If `$ARGUMENTS` is non-empty, use that as the context file destination instead of `docs/project-context.md`.

---

## Step 2 — Configure .claude/settings.local.json

**If the file does not exist**, create `.claude/settings.local.json` with:

```json
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
```

**If the file already exists**, read it and check whether each required field is present:

1. `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` must be `"1"`
2. `permissions.allow` must include all of: `Edit`, `Write`, `Glob`, `Grep`, `Read`, `NotebookEdit`, `Bash(*)`
3. `permissions.deny` must include all of: `Bash(rm -rf *)`, `Bash(git reset --hard*)`, `Bash(git push --force*)`, `Bash(git clean *)`

If any are missing, merge them into the existing file — do NOT overwrite existing entries, only add missing ones. Preserve any other settings the user already has.

Report what was added or changed.

---

## Step 3 — Copy project context template

**If the context file does not exist** at the target path (`docs/project-context.md` or user-specified `$ARGUMENTS`):

1. Create the parent directory if needed
2. Copy the template from `${CLAUDE_SKILL_DIR}/assets/project-context.template.md` to the target path (use the `autonomous-feature-developer` skill's directory)
3. Tell the user to fill it in — the skill won't run without a completed context file

**If the context file already exists**, skip this step and tell the user.

---

## Step 4 — Add context file path to .gitignore check

Check if `.gitignore` exists. If it does, verify that `.claude/` is listed. If not, suggest adding it (but do NOT modify .gitignore without asking — the user may have their own preferences).

---

## Step 5 — Summary

Display a summary of what was done:

```
Autonomous Feature Developer — project initialized

  Settings:    .claude/settings.local.json [created | updated | already configured]
  Context:     docs/project-context.md [created from template | already exists]

Next steps:
  1. Fill in docs/project-context.md with your project's stack, build commands, and conventions
  2. Run: /auto-dev <feature description>
```

If the context file was freshly created, emphasize that filling it in is required before `/auto-dev` will work.
