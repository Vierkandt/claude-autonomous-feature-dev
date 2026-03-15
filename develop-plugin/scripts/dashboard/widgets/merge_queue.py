"""MergeQueueBar widget — current merge queue status."""

from __future__ import annotations

from textual.widgets import Static
from rich.text import Text
from rich.panel import Panel

from ..models import SwarmState


class MergeQueueBar(Static):
    """Shows the current merge queue status."""

    def __init__(self, state: SwarmState | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = state or SwarmState()

    def update_state(self, state: SwarmState) -> None:
        """Update with new state and re-render."""
        self._state = state
        self.refresh()

    def render(self):
        s = self._state
        t = Text()
        t.append("  Merge Queue: ", style="bold")

        # Determine merge queue status from current wave
        current_wave = s.waves.get(s.current_wave)
        if current_wave is None:
            t.append("idle", style="dim")
            return Panel(t, border_style="bright_black", padding=(0, 1))

        if current_wave.status == "completed":
            # Wave done, check if there's a next wave
            next_wave = s.current_wave + 1
            if next_wave <= s.total_waves:
                t.append("idle", style="dim")
                t.append("  \u2502  ", style="dim")
                t.append("Next: ", style="bold")
                t.append(f"waiting for Wave {next_wave} agents to finish", style="yellow")
            else:
                t.append("complete", style="green")
                t.append("  \u2502  ", style="dim")
                t.append("All waves merged", style="green")
        elif current_wave.status == "in-progress":
            wbs = current_wave.workbranches
            merged_count = sum(1 for wb in wbs.values() if wb.status == "merged")
            done_count = sum(
                1 for wb in wbs.values()
                if wb.status in ("merged", "failed")
            )
            total = len(wbs)
            in_progress_count = sum(1 for wb in wbs.values() if wb.status == "in-progress")

            if merged_count > 0 and done_count < total:
                # Some merged, not all resolved (merged+failed < total) — queue is active
                next_to_merge = None
                for slug in current_wave.merge_order:
                    wb = wbs.get(slug)
                    if wb and wb.status not in ("merged", "failed"):
                        next_to_merge = wb
                        break

                if next_to_merge:
                    t.append("active", style="yellow bold")
                    t.append("  \u2502  ", style="dim")
                    t.append("Next: ", style="bold")
                    t.append(next_to_merge.name, style="yellow")
                    if next_to_merge.pr_number:
                        t.append(f" (PR {next_to_merge.pr_number})", style="cyan")
                else:
                    t.append("active", style="yellow bold")
                    t.append(f"  ({merged_count}/{total} merged)", style="dim")
            elif in_progress_count > 0:
                t.append("idle", style="dim")
                t.append("  \u2502  ", style="dim")
                t.append("Next: ", style="bold")
                t.append(f"waiting for Wave {s.current_wave} agents to finish", style="yellow")
            else:
                t.append("idle", style="dim")
        else:
            t.append("idle", style="dim")

        return Panel(t, border_style="bright_black", padding=(0, 1))
