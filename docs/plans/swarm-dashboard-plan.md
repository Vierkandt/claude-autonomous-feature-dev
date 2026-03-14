# Swarm Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python TUI dashboard that visualizes swarm execution in real-time by watching the filesystem state files that `/swarm` already produces.

**Architecture:** A Textual app watches `docs/workbranches/<slug>/` for state changes (swarm-state.json, phase1 reports, done markers). It renders wave progress, agent status, merge queue state, and running metrics. Ships as `scripts/dashboard.py` in the plugin, launched by the user in a separate terminal.

**Tech Stack:** Python 3.10+, Textual 0.x/1.x, watchfiles, Rich (bundled with Textual)

---

## File Structure

```
develop-plugin/
└── scripts/
    └── dashboard/
        ├── __main__.py          # Entry point: python -m dashboard <plan-slug>
        ├── app.py               # SwarmDashboard App class, screen composition, keybindings
        ├── state.py             # SwarmStateReader — reads/parses all state files into a unified model
        ├── models.py            # Dataclasses: SwarmState, WaveState, WorkbranchState, TransitionResult
        ├── widgets/
        │   ├── __init__.py
        │   ├── header.py        # SwarmHeader — platform name, elapsed time, key metrics
        │   ├── wave_panel.py    # WavePanel — one wave's workbranches with progress bars
        │   ├── merge_queue.py   # MergeQueueBar — current merge queue status
        │   └── detail_panel.py  # DetailPanel — expanded view of selected workbranch (logs, errors, contract deviations)
        └── css/
            └── dashboard.tcss   # Textual CSS stylesheet
```

**Why this structure:**
- `models.py` separates data from rendering — widgets don't parse JSON
- `state.py` encapsulates all filesystem watching — widgets just receive model objects
- Each widget is its own file (Textual convention, keeps context small)
- `__main__.py` allows `python -m dashboard my-slug` invocation
- CSS in a separate `.tcss` file (Textual best practice)

---

## Data Flow

```
Filesystem (written by /swarm)         State Reader              Widgets
─────────────────────────────          ─────────────             ───────
swarm-state.json           ──┐
*-phase1-report.json       ──┼──→  SwarmStateReader  ──→  SwarmState model  ──→  render()
*-phase1-resolution.json   ──┤     (watches files,        (dataclasses)
*-done.json                ──┤      parses, merges)
docs/wave-learnings.md     ──┤
docs/project-contract.md   ──┘
                                        │
                                  FileWatcher (watchfiles)
                                  fires callback on change
                                        │
                                        ▼
                                  app.refresh_state()
                                  (re-reads, re-renders)
```

**Polling vs watching:** Use `watchfiles` for instant updates. Fall back to 5-second polling if `watchfiles` is unavailable (it requires a native extension that may not install on all systems).

---

## SwarmState Model

```python
@dataclass
class WorkbranchState:
    slug: str
    name: str                    # Display name from workbranch file heading
    status: str                  # pending | in-progress | merged | failed | blocked
    phase: str                   # Phase 0-5, done, or —
    phase_detail: str            # Human-readable detail of current activity
    sub_features_done: int
    sub_features_total: int
    pr_number: str
    pr_url: str
    review_iterations: int
    contract_deviations: list[str]
    error: str                   # Non-empty if failed
    blocked_by: str              # Slug of blocking workbranch, if blocked

@dataclass
class TransitionResult:
    issues_found: int
    issues_auto_fixed: int
    major_warnings: int
    contract_updates: int
    learnings_added: int

@dataclass
class WaveState:
    number: int
    status: str                  # pending | in-progress | completed
    workbranches: dict[str, WorkbranchState]
    transition: TransitionResult | None
    merge_order: list[str]       # Slugs in merge priority order

@dataclass
class SwarmState:
    platform_name: str
    plan_slug: str
    status: str                  # running | halted | completed
    started_at: str
    current_wave: int
    total_waves: int
    waves: dict[int, WaveState]
    contract_updates_total: int
    learnings_total: int
    failed_features: list[str]
    blocked_features: list[str]
    tags: list[str]
    halt_reason: str
    integration_pr_url: str
    report_path: str
```

---

## State Reader Logic

The `SwarmStateReader` builds a `SwarmState` by composing data from multiple files:

### Primary source: `swarm-state.json`
- Provides: status, current_wave, waves_completed, wave_results, failed/blocked features, tags
- Missing: per-agent phase detail, sub-feature progress (not in state file)

### Supplementary sources (fill the gaps):

| File | What it tells us |
|---|---|
| `<slug>-phase1-report.json` exists | Agent finished Phase 1 |
| `<slug>-phase1-resolution.json` exists | Orchestrator resolved conflicts, agent proceeding to Phase 2 |
| `<slug>-done.json` exists | Agent finished entirely; read for pr_url, review_iterations, error |
| `<slug>-done.json` absent + phase1 report present | Agent is in Phase 2-5 |
| `<slug>-done.json` absent + no phase1 report | Agent is in Phase 0-1 |
| Workbranch `.md` file `Status:` field | Canonical status set by /swarm |

### Phase inference heuristic

Since agents don't write intermediate phase markers (only phase1-report and done), the dashboard infers:

| Files present | Inferred phase |
|---|---|
| Neither phase1-report nor done | Phase 0 or 1 (show "Phase 0-1") |
| phase1-report exists, no resolution | Phase 1 sync (waiting) |
| phase1-report + resolution exist, no done | Phase 2-4 (show "Phase 2+") |
| done exists with status "merged" | Complete |
| done exists with status "failed" | Failed |

**Sub-feature progress:** Not directly available from filesystem. The dashboard shows sub-feature counts from the workbranch file (total) and estimates progress based on phase (Phase 1 = 0, Phase 2+ = partial, done = all).

For more granular progress, a future enhancement could have agents write a `<slug>-progress.json` file after each sub-feature commit.

---

## Keybindings

| Key | Action |
|---|---|
| `q` | Quit dashboard |
| `r` | Force refresh (re-read all files) |
| `d` | Toggle detail panel for selected workbranch |
| `↑/↓` | Navigate workbranches |
| `Enter` | Open PR URL in browser (if merged/in-progress) |
| `l` | Show wave learnings |
| `c` | Show current contract |
| `e` | Show error detail for failed workbranch |

---

## Tasks

### Task 1: Models and State Reader

**Files:**
- Create: `develop-plugin/scripts/dashboard/models.py`
- Create: `develop-plugin/scripts/dashboard/state.py`

- [ ] **Step 1: Create models.py with all dataclasses**

Write the four dataclasses (`WorkbranchState`, `TransitionResult`, `WaveState`, `SwarmState`) with type hints and default values. Include a `SwarmState.elapsed()` method that computes elapsed time from `started_at`.

- [ ] **Step 2: Create state.py with SwarmStateReader**

Write `SwarmStateReader.__init__(self, plan_slug: str, base_dir: str = ".")` that stores the paths:
- `docs/workbranches/{plan_slug}/swarm-state.json`
- `docs/workbranches/{plan_slug}/` (for glob patterns)

Write `SwarmStateReader.read() -> SwarmState` that:
1. Reads and parses `swarm-state.json` (return a "not started" state if missing)
2. Globs for `*-phase1-report.json`, `*-phase1-resolution.json`, `*-done.json`
3. Reads each workbranch `.md` file to get name, sub-feature count, status
4. Merges everything into a `SwarmState` using the phase inference heuristic
5. Reads `docs/wave-learnings.md` to count total learnings

- [ ] **Step 3: Create `__init__.py` files**

Create empty `develop-plugin/scripts/dashboard/__init__.py` and `develop-plugin/scripts/dashboard/widgets/__init__.py`.

- [ ] **Step 4: Commit**

```bash
git add develop-plugin/scripts/dashboard/
git commit -m "feat(dashboard): add data models and state reader"
```

---

### Task 2: Header Widget

**Files:**
- Create: `develop-plugin/scripts/dashboard/widgets/header.py`

- [ ] **Step 1: Write SwarmHeader widget**

A `Static` widget that renders a Rich `Panel` containing:
- Row 1: Platform name (bold), elapsed time, status counts (✓ merged, ⚙ in-progress, ⏸ blocked, ✗ failed, ○ pending)
- Row 2: Contract updates count, learnings count, wave N/total, swarm status

The widget takes a `SwarmState` and re-renders when `update(state)` is called.

- [ ] **Step 2: Commit**

```bash
git add develop-plugin/scripts/dashboard/widgets/header.py
git commit -m "feat(dashboard): add header widget"
```

---

### Task 3: Wave Panel Widget

**Files:**
- Create: `develop-plugin/scripts/dashboard/widgets/wave_panel.py`

- [ ] **Step 1: Write WavePanel widget**

A `Static` widget that renders one wave as a Rich `Panel`:
- Wave header: icon (✓/▶/○), "Wave N", progress bar (█/░), merge count
- Per-workbranch rows: status icon, name, phase, sub-feature progress bar, PR link
- Detail lines: phase_detail for in-progress agents, blocked_by for blocked agents
- Transition summary: issues, fixes, contract updates, learnings (if wave completed)

Border color: green (completed), yellow (in-progress), dim (pending).

Takes a `WaveState` and re-renders on `update(wave_state)`.

- [ ] **Step 2: Commit**

```bash
git add develop-plugin/scripts/dashboard/widgets/wave_panel.py
git commit -m "feat(dashboard): add wave panel widget"
```

---

### Task 4: Merge Queue and Detail Widgets

**Files:**
- Create: `develop-plugin/scripts/dashboard/widgets/merge_queue.py`
- Create: `develop-plugin/scripts/dashboard/widgets/detail_panel.py`

- [ ] **Step 1: Write MergeQueueBar widget**

A `Static` widget showing:
- "Merge Queue: idle" when no merging is happening
- "Merge Queue: merging <name> (PR #N) — rebasing onto <base>" during merges
- "Merge Queue: conflict in <file> — resolving" during conflict resolution

Inferred from swarm-state.json's wave_results: if current wave's workbranches have some "merged" and some not, the queue is active.

- [ ] **Step 2: Write DetailPanel widget**

A collapsible panel that shows expanded info for a selected workbranch:
- Full sub-features list with checkmarks for completed ones
- Error message (if failed)
- Contract deviations list
- PR URL (clickable link text)

Hidden by default, toggled with `d` key.

- [ ] **Step 3: Commit**

```bash
git add develop-plugin/scripts/dashboard/widgets/
git commit -m "feat(dashboard): add merge queue and detail panel widgets"
```

---

### Task 5: App Shell, CSS, and Entry Point

**Files:**
- Create: `develop-plugin/scripts/dashboard/app.py`
- Create: `develop-plugin/scripts/dashboard/css/dashboard.tcss`
- Create: `develop-plugin/scripts/dashboard/__main__.py`

- [ ] **Step 1: Write dashboard.tcss**

Textual CSS for layout:
- Header: fixed at top, auto height
- Wave panels: scrollable vertical container, auto height each
- Merge queue bar: fixed at bottom above footer
- Detail panel: right sidebar, 40 chars wide, hidden by default
- Footer: keybindings bar

- [ ] **Step 2: Write app.py**

`SwarmDashboard(App)` with:
- `compose()`: yields Header, SwarmHeader, Vertical(wave panels), MergeQueueBar, Footer
- `on_mount()`: start the file watcher or polling timer
- `refresh_state()`: called by watcher/timer, reads state, updates all widgets
- `action_quit()`, `action_refresh()`, `action_toggle_detail()`
- `action_open_pr()`: opens PR URL in default browser
- `action_show_learnings()`: shows wave-learnings.md content in a modal
- `action_show_contract()`: shows project-contract.md in a modal

File watching:
```python
try:
    from watchfiles import awatch
    # Use async watcher
except ImportError:
    # Fall back to polling with set_interval
```

- [ ] **Step 3: Write __main__.py**

```python
"""Usage: python -m dashboard <plan-slug> [--base-dir <path>]"""
import argparse
from .app import SwarmDashboard

parser = argparse.ArgumentParser()
parser.add_argument("plan_slug")
parser.add_argument("--base-dir", default=".")
args = parser.parse_args()

app = SwarmDashboard(plan_slug=args.plan_slug, base_dir=args.base_dir)
app.run()
```

- [ ] **Step 4: Commit**

```bash
git add develop-plugin/scripts/dashboard/
git commit -m "feat(dashboard): add app shell, CSS, and entry point"
```

---

### Task 6: Integration with Plugin

**Files:**
- Modify: `develop-plugin/commands/swarm.md`
- Modify: `develop-plugin/commands/init.md`

- [ ] **Step 1: Add dashboard launch hint to /swarm**

After Step 8 (print execution plan), add a note:

```
To monitor this swarm in real-time, open a second terminal and run:
  python -m dashboard <PLAN_SLUG> --base-dir <PROJECT_ROOT>
```

- [ ] **Step 2: Add dashboard to /init dependency check**

In the `/init` summary, add:

```
Optional: pip install textual watchfiles  (for real-time swarm dashboard)
```

- [ ] **Step 3: Add requirements note**

Create `develop-plugin/scripts/dashboard/requirements.txt`:

```
textual>=0.40.0
watchfiles>=0.20.0
rich>=13.0.0
```

- [ ] **Step 4: Commit**

```bash
git add develop-plugin/scripts/dashboard/requirements.txt develop-plugin/commands/swarm.md develop-plugin/commands/init.md
git commit -m "feat(dashboard): integrate with /swarm and /init commands"
```

---

### Task 7: Delete demo script, clean up

**Files:**
- Delete: `scripts/dashboard-demo.py`
- Delete: `docs/dashboard-screenshot.svg`

- [ ] **Step 1: Remove demo files**

```bash
rm scripts/dashboard-demo.py docs/dashboard-screenshot.svg
```

- [ ] **Step 2: Final commit**

```bash
git add -A
git commit -m "chore: remove dashboard demo, clean up"
```

---

## Summary

| Task | What it produces | Depends on |
|---|---|---|
| 1. Models + State Reader | `models.py`, `state.py` | Nothing |
| 2. Header Widget | `widgets/header.py` | Task 1 |
| 3. Wave Panel Widget | `widgets/wave_panel.py` | Task 1 |
| 4. Merge Queue + Detail | `widgets/merge_queue.py`, `widgets/detail_panel.py` | Task 1 |
| 5. App Shell + Entry Point | `app.py`, `dashboard.tcss`, `__main__.py` | Tasks 1-4 |
| 6. Plugin Integration | Modify swarm.md, init.md, add requirements.txt | Task 5 |
| 7. Cleanup | Remove demo files | Task 6 |

Tasks 2, 3, 4 are independent and can run in parallel after Task 1.
