"""DetailPanel widget — expanded view of selected workbranch."""

from __future__ import annotations

import re
from pathlib import Path

from textual.widgets import Static
from rich.text import Text
from rich.panel import Panel
from rich.console import Group

from ..models import WorkbranchState


class DetailPanel(Static):
    """Collapsible panel showing expanded info for a selected workbranch."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._workbranch: WorkbranchState | None = None
        self._visible = False

    def update_workbranch(self, wb: WorkbranchState | None) -> None:
        """Update with a new workbranch and re-render."""
        self._workbranch = wb
        self.refresh()

    def toggle(self) -> None:
        """Toggle visibility."""
        self._visible = not self._visible
        self.display = self._visible
        self.refresh()

    @property
    def is_visible(self) -> bool:
        return self._visible

    def show(self) -> None:
        self._visible = True
        self.display = True
        self.refresh()

    def hide(self) -> None:
        self._visible = False
        self.display = False
        self.refresh()

    def render(self):
        wb = self._workbranch
        if wb is None:
            return Panel(
                Text("No workbranch selected", style="dim"),
                title="Detail",
                border_style="bright_black",
                padding=(1, 2),
            )

        rows: list[Text] = []

        # Name and status
        name_text = Text()
        name_text.append(wb.name, style="bold white")
        name_text.append(f"  ({wb.status})", style="green" if wb.status == "merged" else "yellow" if wb.status == "in-progress" else "red" if wb.status in ("failed", "blocked") else "dim")
        rows.append(name_text)
        rows.append(Text())

        # Phase
        phase_text = Text()
        phase_text.append("Phase: ", style="bold")
        phase_text.append(wb.phase, style="cyan")
        if wb.phase_detail:
            phase_text.append(f"  \u2014  {wb.phase_detail}", style="dim")
        rows.append(phase_text)

        # Sub-features progress
        sf_text = Text()
        sf_text.append("Sub-features: ", style="bold")
        sf_text.append(f"{wb.sub_features_done}/{wb.sub_features_total}", style="white")
        if wb.sub_features_total > 0:
            sf_fill = int(20 * wb.sub_features_done / wb.sub_features_total)
            sf_text.append("  ")
            sf_text.append("\u2588" * sf_fill, style="green")
            sf_text.append("\u2591" * (20 - sf_fill), style="bright_black")
        rows.append(sf_text)
        rows.append(Text())

        # PR info
        if wb.pr_url:
            pr_text = Text()
            pr_text.append("PR: ", style="bold")
            pr_text.append(wb.pr_url, style="cyan underline")
            rows.append(pr_text)

        if wb.pr_number:
            pr_num_text = Text()
            pr_num_text.append("PR Number: ", style="bold")
            pr_num_text.append(wb.pr_number, style="cyan")
            rows.append(pr_num_text)

        if wb.review_iterations > 0:
            rev_text = Text()
            rev_text.append("Review iterations: ", style="bold")
            rev_text.append(str(wb.review_iterations), style="white")
            rows.append(rev_text)

        # Error
        if wb.error:
            rows.append(Text())
            err_text = Text()
            err_text.append("Error: ", style="bold red")
            err_text.append(wb.error, style="red")
            rows.append(err_text)

        # Contract deviations
        if wb.contract_deviations:
            rows.append(Text())
            dev_header = Text()
            dev_header.append("Contract deviations:", style="bold yellow")
            rows.append(dev_header)
            for deviation in wb.contract_deviations:
                dev_text = Text()
                dev_text.append(f"  \u2022 {deviation}", style="yellow")
                rows.append(dev_text)

        # Blocked by
        if wb.blocked_by:
            rows.append(Text())
            blocked_text = Text()
            blocked_text.append("Blocked by: ", style="bold red")
            blocked_text.append(wb.blocked_by, style="red")
            rows.append(blocked_text)

        # Bug report
        if wb.has_bug_report and wb.bug_report_path:
            rows.append(Text())
            report_header = Text()
            report_header.append("Bug Report:", style="bold yellow")
            rows.append(report_header)

            report_content = self._read_bug_report(wb.bug_report_path)
            if report_content:
                for line in report_content:
                    rows.append(Text(line, style="yellow"))
            else:
                rows.append(Text(f"  (report at {wb.bug_report_path})", style="dim"))

        return Panel(
            Group(*rows),
            title=f"Detail \u2014 {wb.slug}",
            border_style="bright_blue",
            padding=(1, 2),
        )

    @staticmethod
    def _read_bug_report(path: str) -> list[str]:
        """Read a bug report and extract the Error and Root cause analysis sections."""
        try:
            content = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []

        lines: list[str] = []
        # Extract ## Error and ## Root cause analysis sections
        for section_name in ("Error", "Root cause analysis"):
            pattern = rf"^## {re.escape(section_name)}\s*\n(.*?)(?=\n## |\Z)"
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                section_lines = match.group(1).strip().splitlines()
                lines.append(f"  [{section_name}]")
                for sl in section_lines[:20]:
                    lines.append(f"  {sl}")
                lines.append("")

        return lines
