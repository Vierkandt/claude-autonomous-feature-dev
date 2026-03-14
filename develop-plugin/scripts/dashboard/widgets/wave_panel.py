"""WavePanel widget — one wave's workbranches with progress bars."""

from __future__ import annotations

from textual.widgets import Static
from rich.text import Text
from rich.panel import Panel
from rich.console import Group

from ..models import WaveState


STATUS_ICONS = {
    "merged": ("\u2713", "green"),
    "in-progress": ("\u2699", "yellow"),
    "blocked": ("\u23f8", "red"),
    "failed": ("\u2717", "red"),
    "pending": ("\u25cb", "dim"),
    "done": ("\u2713", "green"),
}

PHASE_COLORS = {
    "Phase 0-1": "cyan",
    "Phase 1 sync": "blue",
    "Phase 2+": "yellow",
    "done": "green",
    "failed": "red",
    "\u2014": "dim",
}


class WavePanel(Static):
    """Renders one wave's worth of workbranch status."""

    def __init__(self, wave_state: WaveState | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._wave = wave_state or WaveState()

    def update_state(self, wave_state: WaveState) -> None:
        """Update with new wave state and re-render."""
        self._wave = wave_state
        self.refresh()

    def render(self):
        wd = self._wave
        wbs = wd.workbranches
        total = len(wbs)
        merged = sum(1 for w in wbs.values() if w.status == "merged")
        failed = sum(1 for w in wbs.values() if w.status == "failed")

        # Wave header with progress bar
        if wd.status == "completed":
            bar_fill = "\u2588" * 30
            bar_empty = ""
            pct_style = "green"
        elif wd.status == "in-progress":
            done_count = merged + failed
            fill_len = int(30 * done_count / max(total, 1))
            bar_fill = "\u2588" * fill_len
            bar_empty = "\u2591" * (30 - fill_len)
            pct_style = "yellow"
        else:
            bar_fill = ""
            bar_empty = "\u2591" * 30
            pct_style = "dim"

        # Status icon for wave
        wave_icon_map = {
            "completed": ("\u2713", "green"),
            "in-progress": ("\u25b6", "yellow"),
            "pending": ("\u25cb", "dim"),
        }
        w_icon, w_style = wave_icon_map.get(wd.status, ("?", "white"))

        header = Text()
        header.append(f" {w_icon} ", style=w_style)
        header.append(f"Wave {wd.number} ", style=f"bold {w_style}")
        header.append(bar_fill, style="green")
        header.append(bar_empty, style="bright_black")
        header.append(f" {merged}/{total}", style=pct_style)

        # Workbranch rows
        rows: list[Text] = [header, Text()]
        for name, wb in wbs.items():
            icon, color = STATUS_ICONS.get(wb.status, ("?", "white"))
            phase_color = PHASE_COLORS.get(wb.phase, "white")

            row = Text()
            row.append(f"   {icon} ", style=color)
            row.append(f"{wb.name:<18}", style=f"bold {color}")

            if wb.status == "merged":
                row.append("merged  ", style="green")
                if wb.pr_number:
                    row.append(f"PR {wb.pr_number}  ", style="cyan")
                if wb.review_iterations:
                    suffix = "s" if wb.review_iterations != 1 else ""
                    row.append(f"({wb.review_iterations} review{suffix})", style="dim")
            elif wb.status == "in-progress":
                row.append(f"{wb.phase:<12}", style=phase_color)

                # Sub-feature progress bar
                sf_done = wb.sub_features_done
                sf_total = wb.sub_features_total
                if sf_total > 0:
                    sf_fill = int(10 * sf_done / sf_total)
                else:
                    sf_fill = 0
                row.append("\u2593" * sf_fill, style=phase_color)
                row.append("\u2591" * (10 - sf_fill), style="bright_black")
                row.append(f" {sf_done}/{sf_total}", style=phase_color)
            elif wb.status == "failed":
                row.append("FAILED  ", style="red bold")
                if wb.error:
                    row.append(wb.error[:40], style="red dim")
            elif wb.status == "blocked":
                row.append(wb.phase_detail, style="red dim")
            elif wb.status == "pending":
                row.append(wb.phase_detail, style="dim")

            rows.append(row)

            # Detail line for in-progress agents
            if wb.status == "in-progress" and wb.phase_detail:
                detail = Text()
                detail.append(f"     \u2514\u2500 {wb.phase_detail}", style="dim")
                rows.append(detail)

        # Transition summary (for completed waves)
        if wd.transition:
            tr = wd.transition
            rows.append(Text())
            tr_line = Text()
            tr_line.append("   \u21b3 transition: ", style="dim")
            tr_line.append(
                f"{tr.issues_found} issues",
                style="yellow" if tr.issues_found > 0 else "green",
            )
            tr_line.append(f", {tr.issues_auto_fixed} fixed", style="green")
            tr_line.append(f", {tr.contract_updates} contract updates", style="cyan")
            tr_line.append(f", {tr.learnings_added} learnings", style="blue")
            rows.append(tr_line)

        border_style = {
            "completed": "green",
            "in-progress": "yellow",
            "pending": "bright_black",
        }.get(wd.status, "white")

        return Panel(
            Group(*rows),
            border_style=border_style,
            padding=(0, 1),
        )
