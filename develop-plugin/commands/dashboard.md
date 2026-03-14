---
name: dashboard
description: Launch the real-time swarm dashboard TUI in a new terminal. Shows wave progress, agent status, merge queue, and metrics. Auto-detects plan slug if only one swarm exists. Usage: /dashboard [plan-slug]
argument-hint: "[plan-slug]"
user-invocable: true
allowed-tools: Read, Bash, Glob
---

## Step 1 — Check dependencies

```bash
python -c "import textual; print('OK')" 2>/dev/null || echo "MISSING"
```

If output is `MISSING`, tell the user:

```
The dashboard requires the textual package. Install it with:
  pip install textual watchfiles
Then re-run /dashboard.
```

Stop here if missing.

## Step 2 — Resolve plan slug

If `$ARGUMENTS` is non-empty, use it as the plan slug.

If `$ARGUMENTS` is empty, auto-detect:

```bash
find docs/workbranches -maxdepth 1 -mindepth 1 -type d 2>/dev/null | while read -r d; do basename "$d"; done
```

- If exactly one directory is found, use its name as the plan slug.
- If multiple directories are found, list them and ask: "Multiple swarm workspaces found. Which one? (pick a name)"
- If no directories are found: "No swarm workspaces found in docs/workbranches/. Run /swarm first."

## Step 3 — Verify swarm state exists

```bash
[ -d "docs/workbranches/${PLAN_SLUG}" ] && echo "OK" || echo "MISSING"
```

If `MISSING`: "No workbranch directory found for slug '${PLAN_SLUG}'. Check the name and try again."

## Step 4 — Find the dashboard script

```bash
DASHBOARD_PATH="${CLAUDE_PLUGIN_ROOT}/scripts/dashboard"
[ -d "$DASHBOARD_PATH" ] && echo "FOUND" || echo "NOT_FOUND"
```

If `NOT_FOUND`, fall back to searching:

```bash
find ~/.claude/plugins -path "*/dashboard/__main__.py" -print -quit 2>/dev/null
```

If still not found: "Dashboard script not found. The plugin may need to be updated. Try: /plugin marketplace update claude-autonomous-feature-dev"

## Step 5 — Launch the dashboard

Tell the user to run this command in a separate terminal:

```
python -m dashboard <PLAN_SLUG> --base-dir "<CURRENT_WORKING_DIRECTORY>"
```

With the PYTHONPATH set:

**PowerShell:**
```
$env:PYTHONPATH="<DASHBOARD_PATH>/.."; python -m dashboard <PLAN_SLUG> --base-dir "<CWD>"
```

**Bash / Git Bash:**
```
PYTHONPATH="<DASHBOARD_PATH>/.." python -m dashboard <PLAN_SLUG> --base-dir "<CWD>"
```

Replace `<DASHBOARD_PATH>`, `<PLAN_SLUG>`, and `<CWD>` with the actual resolved values.

Also attempt to launch it directly in the background:

```bash
PYTHONPATH="${DASHBOARD_PATH}/.." python -m dashboard "${PLAN_SLUG}" --base-dir "$(pwd)" &
echo "Dashboard launched (PID: $!)"
```

If the background launch fails (no terminal available), the user can use the manual command above.
