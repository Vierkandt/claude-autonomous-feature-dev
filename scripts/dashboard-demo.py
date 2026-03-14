"""
Swarm Dashboard — Demo snapshot with mock data.
Run: python scripts/dashboard-demo.py
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, ProgressBar, DataTable, Label
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
import time


# ── Mock swarm state ──────────────────────────────────────────────

MOCK_STATE = {
    "plan_slug": "pet-grooming-saas",
    "platform_name": "Pet Grooming SaaS",
    "started_at": "2026-03-14T10:22:00Z",
    "status": "running",
    "current_wave": 2,
    "waves_completed": [1],
    "total_waves": 3,
    "contract_updates": 2,
    "learnings_total": 7,
    "waves": {
        "1": {
            "status": "completed",
            "workbranches": {
                "user-auth": {
                    "status": "merged",
                    "phase": "done",
                    "pr_number": "#12",
                    "pr_url": "https://github.com/example/repo/pull/12",
                    "review_iterations": 2,
                    "sub_features_done": 5,
                    "sub_features_total": 5,
                },
                "config-env": {
                    "status": "merged",
                    "phase": "done",
                    "pr_number": "#13",
                    "pr_url": "https://github.com/example/repo/pull/13",
                    "review_iterations": 1,
                    "sub_features_done": 2,
                    "sub_features_total": 2,
                },
            },
            "transition": {
                "issues_found": 1,
                "issues_fixed": 1,
                "contract_updates": 1,
                "learnings": 4,
            },
        },
        "2": {
            "status": "in-progress",
            "workbranches": {
                "dashboard": {
                    "status": "in-progress",
                    "phase": "Phase 2",
                    "phase_detail": "Implementing sub-feature 3/5: appointment calendar component",
                    "pr_number": "",
                    "pr_url": "",
                    "review_iterations": 0,
                    "sub_features_done": 2,
                    "sub_features_total": 5,
                },
                "billing": {
                    "status": "in-progress",
                    "phase": "Phase 1",
                    "phase_detail": "Writing architecture plan — reading project contract",
                    "pr_number": "",
                    "pr_url": "",
                    "review_iterations": 0,
                    "sub_features_done": 0,
                    "sub_features_total": 4,
                },
                "notifications": {
                    "status": "blocked",
                    "phase": "—",
                    "phase_detail": "Blocked by: dashboard",
                    "pr_number": "",
                    "pr_url": "",
                    "review_iterations": 0,
                    "sub_features_done": 0,
                    "sub_features_total": 3,
                },
            },
            "transition": None,
        },
        "3": {
            "status": "pending",
            "workbranches": {
                "analytics": {
                    "status": "pending",
                    "phase": "—",
                    "phase_detail": "Waiting for Wave 2",
                    "pr_number": "",
                    "pr_url": "",
                    "review_iterations": 0,
                    "sub_features_done": 0,
                    "sub_features_total": 6,
                },
                "admin-panel": {
                    "status": "pending",
                    "phase": "—",
                    "phase_detail": "Waiting for Wave 2",
                    "pr_number": "",
                    "pr_url": "",
                    "review_iterations": 0,
                    "sub_features_done": 0,
                    "sub_features_total": 4,
                },
            },
            "transition": None,
        },
    },
}


# ── Status icons ──────────────────────────────────────────────────

STATUS_ICONS = {
    "merged": ("✓", "green"),
    "in-progress": ("⚙", "yellow"),
    "blocked": ("⏸", "red"),
    "failed": ("✗", "red"),
    "pending": ("○", "dim"),
    "done": ("✓", "green"),
}

PHASE_COLORS = {
    "Phase 0": "cyan",
    "Phase 1": "blue",
    "Phase 2": "yellow",
    "Phase 3": "magenta",
    "Phase 4": "red",
    "done": "green",
    "—": "dim",
}


# ── Widgets ───────────────────────────────────────────────────────


class SwarmHeader(Static):
    """Top bar with platform name, elapsed time, and key metrics."""

    def render(self):
        s = MOCK_STATE
        elapsed = "12m 34s"
        total_features = sum(
            len(w["workbranches"]) for w in s["waves"].values()
        )
        merged = sum(
            1
            for w in s["waves"].values()
            for wb in w["workbranches"].values()
            if wb["status"] == "merged"
        )
        failed = sum(
            1
            for w in s["waves"].values()
            for wb in w["workbranches"].values()
            if wb["status"] == "failed"
        )
        blocked = sum(
            1
            for w in s["waves"].values()
            for wb in w["workbranches"].values()
            if wb["status"] == "blocked"
        )
        in_progress = sum(
            1
            for w in s["waves"].values()
            for wb in w["workbranches"].values()
            if wb["status"] == "in-progress"
        )

        t = Table.grid(padding=(0, 2))
        t.add_column(justify="left", ratio=1)
        t.add_column(justify="right")

        title = Text(f"🐝 {s['platform_name']}", style="bold white")
        status_text = Text()
        status_text.append(f"⏱ {elapsed}  ", style="dim")
        status_text.append(f"✓ {merged}", style="green")
        status_text.append(f"  ⚙ {in_progress}", style="yellow")
        status_text.append(f"  ⏸ {blocked}", style="red")
        status_text.append(f"  ✗ {failed}", style="red")
        status_text.append(f"  ○ {total_features - merged - failed - blocked - in_progress}", style="dim")

        t.add_row(title, status_text)

        metrics = Text()
        metrics.append(f"Contract updates: {s['contract_updates']}", style="cyan")
        metrics.append(f"  │  Learnings: {s['learnings_total']}", style="blue")
        metrics.append(
            f"  │  Wave {s['current_wave']}/{s['total_waves']}",
            style="white",
        )

        t.add_row(metrics, Text(f"Status: {s['status']}", style="bold green" if s["status"] == "running" else "bold red"))

        return Panel(t, border_style="bright_blue", padding=(0, 1))


class WavePanel(Static):
    """One wave's worth of workbranch status."""

    def __init__(self, wave_num: str, wave_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.wave_num = wave_num
        self.wave_data = wave_data

    def render(self):
        wd = self.wave_data
        wbs = wd["workbranches"]
        total = len(wbs)
        merged = sum(1 for w in wbs.values() if w["status"] == "merged")
        failed = sum(1 for w in wbs.values() if w["status"] == "failed")

        # Wave header with progress
        if wd["status"] == "completed":
            bar_fill = "█" * 30
            bar_empty = ""
            pct_style = "green"
        elif wd["status"] == "in-progress":
            done_count = merged + failed
            fill_len = int(30 * done_count / max(total, 1))
            bar_fill = "█" * fill_len
            bar_empty = "░" * (30 - fill_len)
            pct_style = "yellow"
        else:
            bar_fill = ""
            bar_empty = "░" * 30
            pct_style = "dim"

        # Status icon for wave
        wave_icon_map = {
            "completed": ("✓", "green"),
            "in-progress": ("▶", "yellow"),
            "pending": ("○", "dim"),
        }
        w_icon, w_style = wave_icon_map.get(wd["status"], ("?", "white"))

        header = Text()
        header.append(f" {w_icon} ", style=w_style)
        header.append(f"Wave {self.wave_num} ", style=f"bold {w_style}")
        header.append(bar_fill, style="green")
        header.append(bar_empty, style="bright_black")
        header.append(f" {merged}/{total}", style=pct_style)

        # Workbranch rows
        rows = [header, Text()]
        for name, wb in wbs.items():
            icon, color = STATUS_ICONS.get(wb["status"], ("?", "white"))
            phase_color = PHASE_COLORS.get(wb["phase"], "white")

            row = Text()
            row.append(f"   {icon} ", style=color)
            row.append(f"{name:<18}", style=f"bold {color}")

            if wb["status"] == "merged":
                row.append(f"merged  ", style="green")
                row.append(f"PR {wb['pr_number']}  ", style="cyan")
                row.append(f"({wb['review_iterations']} review{'s' if wb['review_iterations'] != 1 else ''})", style="dim")
            elif wb["status"] == "in-progress":
                row.append(f"{wb['phase']:<10}", style=phase_color)

                # Sub-feature progress
                sf_done = wb["sub_features_done"]
                sf_total = wb["sub_features_total"]
                sf_fill = int(10 * sf_done / max(sf_total, 1))
                row.append("▓" * sf_fill, style=phase_color)
                row.append("░" * (10 - sf_fill), style="bright_black")
                row.append(f" {sf_done}/{sf_total}", style=phase_color)
            elif wb["status"] == "blocked":
                row.append(wb["phase_detail"], style="red dim")
            elif wb["status"] == "pending":
                row.append(wb["phase_detail"], style="dim")

            rows.append(row)

            # Detail line for in-progress
            if wb["status"] == "in-progress" and wb.get("phase_detail"):
                detail = Text()
                detail.append(f"     └─ {wb['phase_detail']}", style="dim")
                rows.append(detail)

        # Transition summary
        if wd.get("transition"):
            tr = wd["transition"]
            rows.append(Text())
            tr_line = Text()
            tr_line.append("   ↳ transition: ", style="dim")
            tr_line.append(f"{tr['issues_found']} issues", style="yellow" if tr["issues_found"] > 0 else "green")
            tr_line.append(f", {tr['issues_fixed']} fixed", style="green")
            tr_line.append(f", {tr['contract_updates']} contract updates", style="cyan")
            tr_line.append(f", {tr['learnings']} learnings", style="blue")
            rows.append(tr_line)

        border_style = {
            "completed": "green",
            "in-progress": "yellow",
            "pending": "bright_black",
        }.get(wd["status"], "white")

        return Panel(
            Group(*rows),
            border_style=border_style,
            padding=(0, 1),
        )


class MergeQueue(Static):
    """Merge queue status."""

    def render(self):
        t = Text()
        t.append("  Merge Queue: ", style="bold")
        t.append("idle", style="dim")
        t.append("  │  ", style="dim")
        t.append("Next: ", style="bold")
        t.append("waiting for Wave 2 agents to finish", style="yellow")
        return Panel(t, border_style="bright_black", padding=(0, 1))


class SwarmDashboard(App):
    """Swarm real-time dashboard."""

    CSS = """
    Screen {
        background: $surface;
    }
    SwarmHeader {
        height: auto;
        margin: 0 0 1 0;
    }
    WavePanel {
        height: auto;
        margin: 0 0 0 0;
    }
    MergeQueue {
        height: auto;
        margin: 1 0 0 0;
    }
    #wave-container {
        height: 1fr;
        overflow-y: auto;
    }
    Footer {
        background: $primary-background;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("d", "toggle_detail", "Detail"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield SwarmHeader()
        with Vertical(id="wave-container"):
            for wave_num in sorted(MOCK_STATE["waves"].keys()):
                yield WavePanel(wave_num, MOCK_STATE["waves"][wave_num])
        yield MergeQueue()
        yield Footer()

    def action_refresh(self):
        self.notify("Refreshed swarm state", timeout=2)

    def action_toggle_detail(self):
        self.notify("Detail view toggle (not yet implemented)", timeout=2)


if __name__ == "__main__":
    app = SwarmDashboard()
    app.run()
