"""SwarmHeader widget — platform name, elapsed time, key metrics."""

from __future__ import annotations

from textual.widgets import Static
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from ..models import SwarmState


class SwarmHeader(Static):
    """Top bar with platform name, elapsed time, and key metrics."""

    def __init__(self, state: SwarmState | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = state or SwarmState()
        self._tick = 0
        self._last_state_changed = False

    def update_state(self, state: SwarmState) -> None:
        """Update with new state and re-render."""
        self._state = state
        self.refresh()

    def update_tick(self, tick: int, state_changed: bool) -> None:
        self._tick = tick
        self._last_state_changed = state_changed
        self.refresh()

    def render(self):
        s = self._state
        elapsed = s.elapsed()

        # Count statuses across all waves
        total_features = 0
        merged = 0
        failed = 0
        blocked = 0
        in_progress = 0

        for wave in s.waves.values():
            for wb in wave.workbranches.values():
                total_features += 1
                if wb.status == "merged":
                    merged += 1
                elif wb.status == "failed":
                    failed += 1
                elif wb.status == "blocked":
                    blocked += 1
                elif wb.status == "in-progress":
                    in_progress += 1

        pending = total_features - merged - failed - blocked - in_progress

        t = Table.grid(padding=(0, 2))
        t.add_column(justify="left", ratio=1)
        t.add_column(justify="right")

        # Row 1: Platform name and status counts
        title = Text(f"\U0001f41d {s.platform_name}" if s.platform_name else "\U0001f41d Swarm Dashboard", style="bold white")

        # Build refresh countdown bar
        filled = self._tick
        empty = 4 - self._tick
        bar = Text()
        bar.append("\u2593" * (filled + 1), style="cyan")
        bar.append("\u2591" * empty, style="bright_black")

        # Add status flash
        if self._tick == 0 and self._last_state_changed:
            bar.append(" \u2713 updated", style="green")
        elif self._tick == 0:
            bar.append(" \u00b7 no change", style="dim")

        status_text = Text()
        status_text.append(f"\u23f1 {elapsed}  ", style="dim")
        status_text.append(f"\u2713 {merged}", style="green")
        status_text.append(f"  \u2699 {in_progress}", style="yellow")
        status_text.append(f"  \u23f8 {blocked}", style="red")
        status_text.append(f"  \u2717 {failed}", style="red")
        status_text.append(f"  \u25cb {pending}", style="dim")
        status_text.append("  ")
        status_text.append_text(bar)

        t.add_row(title, status_text)

        # Row 2: Contract updates, learnings, wave progress, status
        metrics = Text()
        metrics.append(f"Contract updates: {s.contract_updates_total}", style="cyan")
        metrics.append(f"  \u2502  Learnings: {s.learnings_total}", style="blue")
        metrics.append(
            f"  \u2502  Wave {s.current_wave}/{s.total_waves}",
            style="white",
        )

        status_style = "bold green" if s.status == "running" else "bold red" if s.status in ("halted", "failed") else "bold yellow"
        t.add_row(metrics, Text(f"Status: {s.status}", style=status_style))

        return Panel(t, border_style="bright_blue", padding=(0, 1))
