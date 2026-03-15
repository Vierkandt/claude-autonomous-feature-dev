"""State reader — builds SwarmState from filesystem state files."""

from __future__ import annotations

import glob
import json
import logging
import os
import re
from pathlib import Path

from .models import SwarmState, WaveState, WorkbranchState, TransitionResult


class SwarmStateReader:
    """Reads and parses all swarm state files into a unified SwarmState model."""

    def __init__(self, plan_slug: str, base_dir: str = ".") -> None:
        self.plan_slug = plan_slug
        self.base_dir = Path(base_dir).resolve()
        self.wb_dir = self.base_dir / "docs" / "workbranches" / plan_slug
        self.state_file = self.wb_dir / "swarm-state.json"

    @property
    def watch_dir(self) -> str:
        """Directory to watch for file changes."""
        return str(self.wb_dir)

    def read(self) -> SwarmState:
        """Read all state files and build a SwarmState."""
        state = SwarmState(plan_slug=self.plan_slug)

        # 1. Read swarm-state.json
        raw = self._read_json(self.state_file)
        if raw is None:
            state.status = "not-started"
            return state

        state.status = raw.get("status", "running")
        state.started_at = raw.get("started_at", "")
        state.current_wave = raw.get("current_wave", 1)
        state.failed_features = raw.get("failed_features", [])
        state.blocked_features = raw.get("blocked_features", [])
        state.tags = raw.get("tags", [])
        state.halt_reason = raw.get("halt_reason", "")
        state.integration_pr_url = raw.get("integration_pr_url", "")
        state.report_path = raw.get("report_path", "")

        # 2. Glob for supplementary files
        phase1_reports = self._glob_slugs("*-phase1-report.json", "-phase1-report.json")
        phase1_resolutions = self._glob_slugs("*-phase1-resolution.json", "-phase1-resolution.json")
        done_markers = self._glob_slugs("*-done.json", "-done.json")
        bug_reports = self._glob_slugs("*-bug-report.md", "-bug-report.md")
        done_data: dict[str, dict] = {}
        for slug in done_markers:
            data = self._read_json(self.wb_dir / f"{slug}-done.json")
            if data:
                done_data[slug] = data

        progress_slugs = self._glob_slugs("*-progress.json", "-progress.json")
        progress_data: dict[str, dict] = {}
        for slug in progress_slugs:
            data = self._read_json(self.wb_dir / f"{slug}-progress.json")
            if data:
                progress_data[slug] = data

        # 3. Read workbranch .md files
        wb_files = self._find_workbranch_md_files()
        wb_info: dict[str, dict] = {}
        for path in wb_files:
            info = self._parse_workbranch_md(path)
            if info and info.get("slug"):
                wb_info[info["slug"]] = info

        # 4. Derive platform name from plan file or slug
        plan_path_str = raw.get("plan", "")
        state.platform_name = self._derive_platform_name(plan_path_str)

        # 5. Build wave structure from wave_results and workbranch info
        wave_results = raw.get("wave_results", {})
        waves_completed = raw.get("waves_completed", [])

        # Determine total waves from workbranch files
        all_wave_nums: set[int] = set()
        for info in wb_info.values():
            wn = info.get("wave")
            if wn is not None:
                all_wave_nums.add(wn)
        # Also include waves from wave_results
        for wn_str in wave_results:
            try:
                all_wave_nums.add(int(wn_str))
            except (ValueError, TypeError):
                pass
        if state.current_wave:
            all_wave_nums.add(state.current_wave)

        state.total_waves = max(all_wave_nums) if all_wave_nums else 0

        # Group workbranches by wave
        wave_wbs: dict[int, list[str]] = {}
        for slug, info in wb_info.items():
            wn = info.get("wave", 1)
            wave_wbs.setdefault(wn, []).append(slug)

        # Build WaveState for each wave
        for wn in sorted(all_wave_nums):
            ws = WaveState(number=wn)

            # Determine wave status
            if wn in waves_completed:
                ws.status = "completed"
            elif wn == state.current_wave and state.status == "running":
                ws.status = "in-progress"
            elif wn < state.current_wave:
                ws.status = "completed"
            else:
                ws.status = "pending"

            # Build workbranch states
            slugs = wave_wbs.get(wn, [])
            wr = wave_results.get(str(wn), {})

            for slug in slugs:
                wbs = self._build_workbranch_state(
                    slug,
                    wb_info.get(slug, {}),
                    phase1_reports,
                    phase1_resolutions,
                    done_data,
                    progress_data,
                    wr,
                    state,
                    ws,
                )
                # Check for bug report
                if slug in bug_reports:
                    wbs.has_bug_report = True
                    wbs.bug_report_path = str(self.wb_dir / f"{slug}-bug-report.md")
                ws.workbranches[slug] = wbs

            # Parse transition results
            transition_data = wr.get("_transition")
            if transition_data and isinstance(transition_data, dict):
                ws.transition = TransitionResult(
                    issues_found=transition_data.get("ISSUES_FOUND", 0),
                    issues_auto_fixed=transition_data.get("ISSUES_AUTO_FIXED", 0),
                    major_warnings=transition_data.get("MAJOR_WARNINGS", 0),
                    contract_updates=transition_data.get("CONTRACT_UPDATES", 0),
                    learnings_added=transition_data.get("LEARNINGS_ADDED", 0),
                )

            # Merge order from workbranch priority
            ws.merge_order = sorted(slugs, key=lambda s: self._priority_sort_key(wb_info.get(s, {})))

            state.waves[wn] = ws

        # 6. Count contract updates and learnings
        state.contract_updates_total = self._count_contract_updates(wave_results)
        state.learnings_total = self._count_learnings()

        return state

    def _build_workbranch_state(
        self,
        slug: str,
        info: dict,
        phase1_reports: set[str],
        phase1_resolutions: set[str],
        done_data: dict[str, dict],
        progress_data: dict[str, dict],
        wave_result: dict,
        swarm: SwarmState,
        wave: WaveState,
    ) -> WorkbranchState:
        """Build a WorkbranchState for one workbranch using the phase inference heuristic."""
        wbs = WorkbranchState(slug=slug)
        wbs.name = info.get("name", slug)
        wbs.sub_features_total = info.get("sub_feature_count", 0)

        # Status from wave_result or workbranch file
        wr_status = wave_result.get(slug)
        file_status = info.get("status", "pending")

        if wr_status in ("merged", "failed"):
            wbs.status = wr_status
        elif slug in swarm.failed_features:
            wbs.status = "failed"
        elif slug in swarm.blocked_features:
            wbs.status = "blocked"
        elif file_status and file_status != "pending":
            wbs.status = file_status
        elif wave.status == "in-progress":
            wbs.status = "in-progress"
        else:
            wbs.status = "pending"

        # Done marker data
        if slug in done_data:
            dd = done_data[slug]
            wbs.pr_number = dd.get("pr_number", "")
            wbs.pr_url = dd.get("pr_url", "")
            wbs.review_iterations = dd.get("review_iterations", 0)
            wbs.error = dd.get("error", "")
            wbs.contract_deviations = dd.get("contract_deviations", [])
            done_status = dd.get("status", "")
            if done_status == "failed" and not wbs.error:
                wbs.error = dd.get("reason", "Unknown failure")

        # Phase inference heuristic
        has_phase1 = slug in phase1_reports
        has_resolution = slug in phase1_resolutions
        has_done = slug in done_data

        if has_done:
            if wbs.status == "merged" or (done_data[slug].get("status") == "merged"):
                wbs.phase = "done"
                wbs.phase_detail = "Complete"
                wbs.sub_features_done = wbs.sub_features_total
            elif wbs.status == "failed":
                wbs.phase = "failed"
                wbs.phase_detail = wbs.error or "Failed"
            else:
                wbs.phase = "done"
                wbs.phase_detail = "Finished"
                wbs.sub_features_done = wbs.sub_features_total
        elif has_phase1 and has_resolution:
            wbs.phase = "Phase 2+"
            wbs.phase_detail = "Implementing (post-resolution)"
            # Estimate partial progress
            wbs.sub_features_done = max(1, wbs.sub_features_total // 3)
        elif has_phase1 and not has_resolution:
            wbs.phase = "Phase 1 sync"
            wbs.phase_detail = "Waiting for conflict resolution"
            wbs.sub_features_done = 0
        elif wbs.status == "in-progress":
            wbs.phase = "Phase 0-1"
            wbs.phase_detail = "Planning and architecture"
            wbs.sub_features_done = 0
        elif wbs.status == "blocked":
            wbs.phase = "\u2014"
            blocked_by = info.get("blocked_by", "")
            wbs.blocked_by = blocked_by
            wbs.phase_detail = f"Blocked by: {blocked_by}" if blocked_by else "Blocked"
        elif wbs.status == "pending":
            wbs.phase = "\u2014"
            wbs.phase_detail = f"Waiting for Wave {wave.number}" if wave.status == "pending" else "Pending"
        else:
            wbs.phase = "\u2014"
            wbs.phase_detail = ""

        # Merge progress heartbeat data (supplements, not replaces, existing data)
        if slug in progress_data and slug not in done_data:
            pd = progress_data[slug]
            wbs.current_action = pd.get("current_action", "")
            wbs.files_created = pd.get("files_created", [])
            wbs.files_modified = pd.get("files_modified", [])
            wbs.build_status = pd.get("build_status", "not_run")
            wbs.test_status = pd.get("test_status", "not_run")
            try:
                wbs.commits = int(pd.get("commits", 0))
            except (ValueError, TypeError):
                wbs.commits = 0
            wbs.last_update = pd.get("timestamp", "")
            wbs.progress_errors = pd.get("errors", [])
            # Use sub-feature progress from heartbeat if available
            sf_index = pd.get("sub_feature_index")
            sf_total = pd.get("sub_feature_total")
            if sf_index is not None and sf_total is not None:
                try:
                    wbs.sub_features_done = int(sf_index)
                except (ValueError, TypeError):
                    wbs.sub_features_done = 0
                try:
                    wbs.sub_features_total = int(sf_total)
                except (ValueError, TypeError):
                    wbs.sub_features_total = 0

        return wbs

    def _glob_slugs(self, pattern: str, suffix: str) -> set[str]:
        """Glob for files matching pattern and extract slugs by stripping the suffix."""
        slugs: set[str] = set()
        for path in glob.glob(str(self.wb_dir / pattern)):
            basename = os.path.basename(path)
            if basename.endswith(suffix):
                slug = basename[: -len(suffix)]
                slugs.add(slug)
        return slugs

    def _find_workbranch_md_files(self) -> list[Path]:
        """Find all workbranch .md files, excluding bug reports."""
        results = []
        if not self.wb_dir.exists():
            return results
        for path in self.wb_dir.glob("*.md"):
            if not path.name.endswith("-bug-report.md"):
                results.append(path)
        return results

    def _parse_workbranch_md(self, path: Path) -> dict:
        """Parse a workbranch .md file for name, wave, status, sub-feature count, etc."""
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logging.warning("Cannot read workbranch file %s: %s", path, exc)
            return {}

        info: dict = {}
        # Slug from filename
        info["slug"] = path.stem

        # Name from heading: # Workbranch: <Name>
        heading_match = re.search(r"^#\s+(?:Workbranch:\s*)?(.+)", content, re.MULTILINE)
        if heading_match:
            info["name"] = heading_match.group(1).strip()
        else:
            info["name"] = info["slug"]

        # Wave number
        wave_match = re.search(r"(?:^##\s*Wave\s*$\s*(\d+)|Wave:\s*(\d+))", content, re.MULTILINE)
        if wave_match:
            wn = wave_match.group(1) or wave_match.group(2)
            info["wave"] = int(wn)
        else:
            # Try finding wave as a section with a number on the next line
            wave_section = re.search(r"##\s*Wave\s*\n+(\d+)", content)
            if wave_section:
                info["wave"] = int(wave_section.group(1))
            else:
                info["wave"] = 1

        # Status field
        status_match = re.search(r"Status:\s*(\S+)", content, re.IGNORECASE)
        if status_match:
            info["status"] = status_match.group(1).strip().lower()
        else:
            info["status"] = "pending"

        # Sub-features count: count numbered list items under ## Sub-features
        sub_features_section = re.search(
            r"##\s*Sub-features.*?\n((?:\s*\d+\..+\n?)+)", content, re.IGNORECASE
        )
        if sub_features_section:
            items = re.findall(r"^\s*\d+\.\s+", sub_features_section.group(1), re.MULTILINE)
            info["sub_feature_count"] = len(items)
        else:
            # Also try counting numbered items in Implementation Order or similar
            impl_section = re.search(
                r"##\s*(?:Implementation Order|Sub-features|Features).*?\n((?:\s*\d+\..+\n?)+)",
                content,
                re.IGNORECASE,
            )
            if impl_section:
                items = re.findall(r"^\s*\d+\.\s+", impl_section.group(1), re.MULTILINE)
                info["sub_feature_count"] = len(items)
            else:
                info["sub_feature_count"] = 0

        # Blocked by
        blocked_match = re.search(r"Blocked\s*by:\s*(.+)", content, re.IGNORECASE)
        if blocked_match:
            info["blocked_by"] = blocked_match.group(1).strip()

        # Priority
        priority_match = re.search(r"Priority:\s*(\w+)", content, re.IGNORECASE)
        if priority_match:
            info["priority"] = priority_match.group(1).strip().lower()
        else:
            info["priority"] = "medium"

        return info

    def _derive_platform_name(self, plan_path: str) -> str:
        """Derive a display name from the plan file path or slug."""
        if plan_path:
            basename = os.path.basename(plan_path)
            name = re.sub(r"-plan\.md$", "", basename)
            name = re.sub(r"\.md$", "", name)
            return name.replace("-", " ").title()
        return self.plan_slug.replace("-", " ").title()

    def _priority_sort_key(self, info: dict) -> tuple:
        """Sort key for merge order: high=0, medium=1, low=2, then alphabetical."""
        priority_order = {"high": 0, "medium": 1, "low": 2}
        p = info.get("priority", "medium")
        return (priority_order.get(p, 1), info.get("slug", ""))

    def _count_contract_updates(self, wave_results: dict) -> int:
        """Sum contract updates across all wave transitions."""
        total = 0
        for wr in wave_results.values():
            if isinstance(wr, dict):
                tr = wr.get("_transition", {})
                if isinstance(tr, dict):
                    total += tr.get("CONTRACT_UPDATES", 0)
        return total

    def _count_learnings(self) -> int:
        """Count learnings from docs/wave-learnings.md."""
        learnings_file = self.base_dir / "docs" / "wave-learnings.md"
        if not learnings_file.exists():
            return 0
        try:
            content = learnings_file.read_text(encoding="utf-8")
            # Count "### " headings as individual learnings, or "- " items
            heading_count = len(re.findall(r"^###\s+", content, re.MULTILINE))
            if heading_count > 0:
                return heading_count
            # Fallback: count bullet points
            return len(re.findall(r"^-\s+", content, re.MULTILINE))
        except (OSError, UnicodeDecodeError) as exc:
            logging.warning("Cannot read learnings file: %s", exc)
            return 0

    def _read_json(self, path: Path) -> dict | None:
        """Read and parse a JSON file. Returns None if file does not exist."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logging.warning("Corrupt state file %s: %s", path, exc)
            return None
        except OSError as exc:
            logging.warning("Cannot read state file %s: %s", path, exc)
            return None
