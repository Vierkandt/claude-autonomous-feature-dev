"""Data models for the swarm dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class WorkbranchState:
    """State of a single workbranch (feature agent)."""

    slug: str = ""
    name: str = ""
    status: str = "pending"  # pending | in-progress | merged | failed | blocked
    phase: str = "\u2014"  # Phase 0-5, done, or \u2014
    phase_detail: str = ""  # Human-readable detail of current activity
    sub_features_done: int = 0
    sub_features_total: int = 0
    pr_number: str = ""
    pr_url: str = ""
    review_iterations: int = 0
    contract_deviations: list[str] = field(default_factory=list)
    error: str = ""  # Non-empty if failed
    blocked_by: str = ""  # Slug of blocking workbranch, if blocked
    current_action: str = ""
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    build_status: str = "not_run"
    test_status: str = "not_run"
    commits: int = 0
    last_update: str = ""


@dataclass
class TransitionResult:
    """Results from a wave-transition agent run."""

    issues_found: int = 0
    issues_auto_fixed: int = 0
    major_warnings: int = 0
    contract_updates: int = 0
    learnings_added: int = 0


@dataclass
class WaveState:
    """State of one execution wave."""

    number: int = 0
    status: str = "pending"  # pending | in-progress | completed
    workbranches: dict[str, WorkbranchState] = field(default_factory=dict)
    transition: TransitionResult | None = None
    merge_order: list[str] = field(default_factory=list)  # Slugs in merge priority order


@dataclass
class SwarmState:
    """Top-level swarm execution state."""

    platform_name: str = ""
    plan_slug: str = ""
    status: str = "not-started"  # running | halted | completed | not-started
    started_at: str = ""
    current_wave: int = 0
    total_waves: int = 0
    waves: dict[int, WaveState] = field(default_factory=dict)
    contract_updates_total: int = 0
    learnings_total: int = 0
    failed_features: list[str] = field(default_factory=list)
    blocked_features: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    halt_reason: str = ""
    integration_pr_url: str = ""
    report_path: str = ""

    def elapsed(self) -> str:
        """Compute elapsed time from started_at to now as a human-readable string."""
        if not self.started_at:
            return "0s"
        try:
            start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - start
            total_seconds = int(delta.total_seconds())
            if total_seconds < 0:
                return "0s"
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        except (ValueError, TypeError):
            return "??"
