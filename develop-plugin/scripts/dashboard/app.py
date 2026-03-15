"""SwarmDashboard App — main Textual application."""

from __future__ import annotations

import asyncio
import webbrowser
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static
from rich.text import Text
from rich.panel import Panel

from .models import SwarmState
from .state import SwarmStateReader
from .widgets.header import SwarmHeader
from .widgets.wave_panel import WavePanel
from .widgets.merge_queue import MergeQueueBar
from .widgets.detail_panel import DetailPanel


CSS_PATH = Path(__file__).parent / "css" / "dashboard.tcss"


class LearningsModal(Static):
    """Modal showing wave-learnings.md content."""

    def __init__(self, content: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content

    def render(self):
        return Panel(
            Text(self._content or "No learnings found.", style="white"),
            title="Wave Learnings",
            border_style="blue",
            padding=(1, 2),
        )


class ContractModal(Static):
    """Modal showing project-contract.md content."""

    def __init__(self, content: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content

    def render(self):
        return Panel(
            Text(self._content or "No contract found.", style="white"),
            title="Project Contract",
            border_style="cyan",
            padding=(1, 2),
        )


class ErrorModal(Static):
    """Modal showing error details for a failed workbranch."""

    def __init__(self, content: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content

    def render(self):
        return Panel(
            Text(self._content or "No error details.", style="red"),
            title="Error Detail",
            border_style="red",
            padding=(1, 2),
        )


class SwarmDashboard(App):
    """Swarm real-time dashboard TUI application."""

    CSS_PATH = CSS_PATH

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("d", "toggle_detail", "Detail"),
        ("up", "navigate_up", "Up"),
        ("down", "navigate_down", "Down"),
        ("enter", "open_pr", "Open PR"),
        ("l", "show_learnings", "Learnings"),
        ("c", "show_contract", "Contract"),
        ("e", "show_error", "Error"),
    ]

    def __init__(
        self,
        plan_slug: str,
        base_dir: str = ".",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.reader = SwarmStateReader(plan_slug=plan_slug, base_dir=base_dir)
        self._state = SwarmState(plan_slug=plan_slug)
        self._selected_index = 0
        self._all_workbranches: list[tuple[int, str]] = []  # (wave_num, slug)
        self._watcher_task: asyncio.Task | None = None
        self._use_watchfiles = False
        self._polling_active = False
        self._refresh_counter = 0
        self._refresh_tick = 0
        self._state_changed = False
        self._last_refresh_error: str | None = None
        self._dirty = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield SwarmHeader(self._state, id="swarm-header")
        with Horizontal(id="main-content"):
            with Vertical(id="wave-container"):
                pass  # Wave panels added dynamically
            yield DetailPanel(id="detail-panel")
        yield MergeQueueBar(self._state, id="merge-queue")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize: read state and start file watcher."""
        self._refresh_state()
        self._start_watcher()
        self.set_interval(1.0, self._tick_refresh_timer)

    def _start_watcher(self) -> None:
        """Start file watcher using watchfiles (optional, sets dirty flag)."""
        try:
            from watchfiles import awatch  # noqa: F401
            self._use_watchfiles = True
            self._watcher_task = asyncio.ensure_future(self._watch_files())
        except ImportError:
            self._use_watchfiles = False
            self.notify("watchfiles not installed, using 5s polling", timeout=4)
            self._fallback_to_polling()

    def _fallback_to_polling(self) -> None:
        """Mark that we are in polling-only mode (tick timer handles refresh)."""
        if not self._polling_active:
            self._polling_active = True

    async def _watch_files(self) -> None:
        """Watch the workbranch directory for changes, setting dirty flag.

        If the watcher fails for any reason other than cancellation, the
        dashboard falls back to 5-second polling and notifies the user.
        """
        try:
            from watchfiles import awatch

            watch_path = self.reader.watch_dir
            if not Path(watch_path).exists():
                self._fallback_to_polling()
                return

            async for _changes in awatch(watch_path):
                self._dirty = True
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.notify(
                f"File watcher failed ({exc}), falling back to polling",
                severity="warning",
                timeout=5,
            )
            self._fallback_to_polling()

    def _tick_refresh_timer(self) -> None:
        """Sole timing driver: 1-second tick, refresh every 5 ticks or on dirty."""
        self._refresh_tick = (self._refresh_tick + 1) % 5
        if self._refresh_tick == 0 or self._dirty:
            self._dirty = False
            old_state = self._state
            self._refresh_state()
            self._state_changed = old_state != self._state
            try:
                header = self.query_one("#swarm-header", SwarmHeader)
                header.update_tick(0, self._state_changed)
            except Exception:
                pass
            self._state_changed = False
            self._refresh_tick = 0  # Reset cycle after early dirty refresh
        else:
            try:
                header = self.query_one("#swarm-header", SwarmHeader)
                header.update_tick(self._refresh_tick, False)
            except Exception:
                pass

    def _refresh_state(self) -> None:
        """Re-read state files and update all widgets (no tick/timer logic)."""
        try:
            self._state = self.reader.read()
            self._last_refresh_error = None
        except FileNotFoundError:
            # Expected during startup before state files exist
            pass
        except Exception as exc:
            msg = f"Dashboard refresh error: {exc}"
            if msg != getattr(self, '_last_refresh_error', None):
                self._last_refresh_error = msg
                self.notify(msg, severity="error", timeout=5)

        self._rebuild_workbranch_index()
        self._update_widgets()

    def _rebuild_workbranch_index(self) -> None:
        """Rebuild the flat list of (wave_num, slug) for navigation."""
        self._all_workbranches = []
        for wave_num in sorted(self._state.waves.keys()):
            wave = self._state.waves[wave_num]
            for slug in wave.workbranches:
                self._all_workbranches.append((wave_num, slug))
        # Clamp selected index
        if self._all_workbranches:
            self._selected_index = max(0, min(self._selected_index, len(self._all_workbranches) - 1))
        else:
            self._selected_index = 0

    def _update_widgets(self) -> None:
        """Update all dashboard widgets with current state."""
        # Update header
        header = self.query_one("#swarm-header", SwarmHeader)
        header.update_state(self._state)

        # Update merge queue
        merge_queue = self.query_one("#merge-queue", MergeQueueBar)
        merge_queue.update_state(self._state)

        # Rebuild wave panels with unique IDs to avoid DuplicateIds error
        self._refresh_counter += 1
        container = self.query_one("#wave-container", Vertical)
        container.remove_children()
        for wave_num in sorted(self._state.waves.keys()):
            wave = self._state.waves[wave_num]
            panel = WavePanel(wave, id=f"wave-{wave_num}-r{self._refresh_counter}")
            container.mount(panel)

        # Update detail panel if visible
        detail = self.query_one("#detail-panel", DetailPanel)
        if detail.is_visible and self._all_workbranches:
            wave_num, slug = self._all_workbranches[self._selected_index]
            wave = self._state.waves.get(wave_num)
            if wave:
                wb = wave.workbranches.get(slug)
                detail.update_workbranch(wb)

    def _get_selected_workbranch(self):
        """Get the currently selected workbranch state, or None."""
        if not self._all_workbranches:
            return None
        wave_num, slug = self._all_workbranches[self._selected_index]
        wave = self._state.waves.get(wave_num)
        if wave is None:
            return None
        return wave.workbranches.get(slug)

    # ── Actions ──────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        """Force refresh state."""
        old_state = self._state
        self._refresh_state()
        self._state_changed = old_state != self._state
        self._refresh_tick = 0
        try:
            header = self.query_one("#swarm-header", SwarmHeader)
            header.update_tick(0, self._state_changed)
        except Exception:
            pass
        self._state_changed = False
        self.notify("Refreshed swarm state", timeout=2)

    def action_toggle_detail(self) -> None:
        """Toggle the detail panel."""
        detail = self.query_one("#detail-panel", DetailPanel)
        detail.toggle()
        if detail.is_visible:
            wb = self._get_selected_workbranch()
            detail.update_workbranch(wb)

    def action_navigate_up(self) -> None:
        """Navigate to previous workbranch."""
        if self._all_workbranches and self._selected_index > 0:
            self._selected_index -= 1
            self._update_detail_if_visible()
            self.notify(self._selected_name(), timeout=1)

    def action_navigate_down(self) -> None:
        """Navigate to next workbranch."""
        if self._all_workbranches and self._selected_index < len(self._all_workbranches) - 1:
            self._selected_index += 1
            self._update_detail_if_visible()
            self.notify(self._selected_name(), timeout=1)

    def action_open_pr(self) -> None:
        """Open the selected workbranch's PR in the browser."""
        wb = self._get_selected_workbranch()
        if wb and wb.pr_url:
            webbrowser.open(wb.pr_url)
            self.notify(f"Opening PR: {wb.pr_url}", timeout=2)
        else:
            self.notify("No PR URL available for selected workbranch", timeout=2)

    def action_show_learnings(self) -> None:
        """Show wave-learnings.md content."""
        learnings_path = self.reader.base_dir / "docs" / "wave-learnings.md"
        content = self._read_file(learnings_path)
        if content:
            self.notify(f"Learnings:\n{content[:200]}...", timeout=5)
        else:
            self.notify("No wave-learnings.md found", timeout=2)

    def action_show_contract(self) -> None:
        """Show project-contract.md content."""
        contract_path = self.reader.base_dir / "docs" / "project-contract.md"
        content = self._read_file(contract_path)
        if content:
            self.notify(f"Contract loaded ({len(content)} chars)", timeout=2)
        else:
            self.notify("No project-contract.md found", timeout=2)

    def action_show_error(self) -> None:
        """Show error detail for selected failed workbranch."""
        wb = self._get_selected_workbranch()
        if wb and wb.error:
            self.notify(f"Error ({wb.name}): {wb.error}", timeout=5)
        elif wb:
            self.notify(f"No error for {wb.name}", timeout=2)
        else:
            self.notify("No workbranch selected", timeout=2)

    # ── Helpers ──────────────────────────────────────────────────────

    def _update_detail_if_visible(self) -> None:
        """Update the detail panel if it's visible."""
        detail = self.query_one("#detail-panel", DetailPanel)
        if detail.is_visible:
            wb = self._get_selected_workbranch()
            detail.update_workbranch(wb)

    def _selected_name(self) -> str:
        """Get a display string for the currently selected workbranch."""
        if not self._all_workbranches:
            return ""
        wave_num, slug = self._all_workbranches[self._selected_index]
        wave = self._state.waves.get(wave_num)
        if wave:
            wb = wave.workbranches.get(slug)
            if wb:
                return f"[{self._selected_index + 1}/{len(self._all_workbranches)}] {wb.name}"
        return f"[{self._selected_index + 1}/{len(self._all_workbranches)}] {slug}"

    @staticmethod
    def _read_file(path: Path) -> str:
        """Read a text file, returning empty string on error."""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""
