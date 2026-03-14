"""Entry point: python -m dashboard <plan-slug> [--base-dir <path>]"""

import argparse
import sys

from .app import SwarmDashboard


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Swarm Dashboard — real-time TUI for monitoring swarm execution",
    )
    parser.add_argument(
        "plan_slug",
        help="The plan slug (e.g., pet-grooming-saas)",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project root directory (default: current directory)",
    )
    args = parser.parse_args()

    app = SwarmDashboard(plan_slug=args.plan_slug, base_dir=args.base_dir)
    app.run()


if __name__ == "__main__":
    main()
