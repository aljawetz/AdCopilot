"""CLI for running seeded scenarios through the diagnostic baseline."""

from __future__ import annotations

import argparse
import json
import sys

from adcopilot.engine import diagnose
from adcopilot.explain import explain
from adcopilot.generate import SCENARIOS, generate_campaign


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AdCopilot Sprint 3 baseline: diagnose a seeded synthetic campaign."
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        default="cvr_drop",
        help="Labeled synthetic shock to generate (default: cvr_drop)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured Diagnosis JSON instead of the template explanation",
    )
    args = parser.parse_args(argv)

    days = generate_campaign(args.scenario)
    result = diagnose(days)

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))
    else:
        print(f"Scenario: {args.scenario}")
        print(explain(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
