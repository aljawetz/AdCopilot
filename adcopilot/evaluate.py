"""Score AdCopilot against dashboard and ablation rivals on seeded campaigns."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any

from adcopilot.engine import (
    HIGH_MARGIN,
    HIGH_SHARE,
    baseline_biggest_mover,
    baseline_cpc_cvr,
    diagnose,
)
from adcopilot.generate import (
    BASELINE_DAYS,
    CURRENT_DAYS,
    DEFAULT_NOISE_SIGMA,
    DEFAULT_SEED,
    SCENARIOS,
    expected_label,
    generate_campaign,
    generate_dataset,
)
from adcopilot.metrics import aggregate

SYSTEMS = ("B0", "B1", "B1b", "B2-", "B2")


@dataclass
class EvalResult:
    n: int
    seed: int
    n_per_class: int
    high_share: float
    high_margin: float
    noise_sigma: float
    impressions: float | None
    systems: dict[str, dict[str, float]]
    per_class: dict[str, dict[str, float]] = field(default_factory=dict)


def _empty_stats() -> dict[str, float]:
    return {
        "n": 0.0,
        "detected": 0.0,
        "answered": 0.0,
        "correct": 0.0,
        "true_pos": 0.0,
        "false_pos": 0.0,
        "n_anomaly": 0.0,
        "n_stable": 0.0,
        "amb_detected": 0.0,
        "amb_refused": 0.0,
    }


def _answered(cause: str | None) -> bool:
    return cause is not None and cause != "ambiguous"


def _summarize(stats: dict[str, float]) -> dict[str, float]:
    n = stats["n"] or 1.0
    answered = stats["answered"]
    n_anom = stats["n_anomaly"] or 1.0
    n_stable = stats["n_stable"] or 1.0
    amb_det = stats["amb_detected"]
    coverage = answered / n
    selective = (stats["correct"] / answered) if answered else 0.0
    refusal = (stats["amb_refused"] / amb_det) if amb_det else 0.0
    return {
        "overall_acc": stats["correct"] / n,
        "selective_acc": selective,
        "coverage": coverage,
        "refusal_given_det": refusal,
        "tpr": stats["true_pos"] / n_anom,
        "fpr": stats["false_pos"] / n_stable,
        "n": stats["n"],
        "answered": answered,
        "correct": stats["correct"],
        "amb_detected": amb_det,
    }


def evaluate(
    n_per_class: int = 100,
    *,
    seed: int = DEFAULT_SEED,
    noise_sigma: float = DEFAULT_NOISE_SIGMA,
    impressions: float | None = None,
    high_share: float = HIGH_SHARE,
    high_margin: float = HIGH_MARGIN,
) -> EvalResult:
    tallies = {name: _empty_stats() for name in SYSTEMS}
    per_class = {scenario: _empty_stats() for scenario in SCENARIOS}

    n = 0
    for scenario, _campaign_id, days in generate_dataset(
        n_per_class,
        seed=seed,
        noise_sigma=noise_sigma,
        impressions=impressions,
    ):
        n += 1
        truth = expected_label(scenario)
        truth_anomaly = bool(truth["anomaly"])
        truth_cause = truth["cause"]

        try:
            dx = diagnose(days, high_share=high_share, high_margin=high_margin)
            dx_open = diagnose(
                days,
                refuse=False,
                high_share=high_share,
                high_margin=high_margin,
            )
        except ValueError:
            detected = False
            predictions = {name: None for name in SYSTEMS}
        else:
            detected = dx.anomaly
            if not detected:
                predictions = {name: None for name in SYSTEMS}
            else:
                baseline = aggregate(days[:BASELINE_DAYS])
                current = aggregate(days[BASELINE_DAYS : BASELINE_DAYS + CURRENT_DAYS])
                predictions = {
                    "B0": "cpm",
                    "B1": baseline_cpc_cvr(baseline, current),
                    "B1b": baseline_biggest_mover(baseline, current),
                    "B2-": dx_open.cause,
                    "B2": dx.cause,
                }

        for name, pred in predictions.items():
            _update(tallies[name], truth_anomaly, truth_cause, detected, pred)
        _update(per_class[scenario], truth_anomaly, truth_cause, detected, predictions["B2"])

    return EvalResult(
        n=n,
        seed=seed,
        n_per_class=n_per_class,
        high_share=high_share,
        high_margin=high_margin,
        noise_sigma=noise_sigma,
        impressions=impressions,
        systems={name: _summarize(stats) for name, stats in tallies.items()},
        per_class={name: _summarize(stats) for name, stats in per_class.items()},
    )


def _update(
    stats: dict[str, float],
    truth_anomaly: bool,
    truth_cause: object,
    detected: bool,
    pred: str | None,
) -> None:
    stats["n"] += 1
    if truth_anomaly:
        stats["n_anomaly"] += 1
    else:
        stats["n_stable"] += 1
    if detected:
        stats["detected"] += 1
        if truth_anomaly:
            stats["true_pos"] += 1
        else:
            stats["false_pos"] += 1
        if truth_cause == "ambiguous":
            stats["amb_detected"] += 1
            if pred == "ambiguous":
                stats["amb_refused"] += 1
    if _answered(pred):
        stats["answered"] += 1
        if pred == truth_cause:
            stats["correct"] += 1


def _fmt(row: dict[str, float]) -> str:
    return (
        f"{row['overall_acc']:.3f}  sel {row['selective_acc']:.3f}  "
        f"cov {row['coverage']:.3f}  ref {row['refusal_given_det']:.3f}  "
        f"TPR {row['tpr']:.3f}  FPR {row['fpr']:.3f}"
    )


def _print_result(result: EvalResult, title: str) -> None:
    labels = {
        "B0": "B0 majority (always CPM)",
        "B1": "B1 dashboard CPC vs CVR",
        "B1b": "B1b biggest relative mover",
        "B2-": "B2- AdCopilot, no refusal",
        "B2": "B2 AdCopilot (70/40)",
    }
    print(title)
    print(
        f"n={result.n}  seed={result.seed}  sigma={result.noise_sigma}  "
        f"share={result.high_share:g}  margin={result.high_margin:g}  "
        f"impressions={result.impressions or 'drawn'}"
    )
    for name in SYSTEMS:
        label = labels[name]
        if name == "B2":
            label = f"B2 AdCopilot ({result.high_share:g}/{result.high_margin:g})"
        print(f"  {label:<32} {_fmt(result.systems[name])}")
    print("  per-class B2:")
    for scenario in SCENARIOS:
        row = result.per_class[scenario]
        print(
            f"    {scenario:<16} overall {row['overall_acc']:.3f}  "
            f"sel {row['selective_acc']:.3f}  cov {row['coverage']:.3f}  "
            f"TPR {row['tpr']:.3f}"
        )
    print()


def find_ctr_gap_example(seed: int = DEFAULT_SEED, limit: int = 200) -> dict[str, Any] | None:
    """Find a CTR-drop campaign where the dashboard rival calls CPM and we call CTR."""
    for campaign_id in range(limit):
        days = generate_campaign("ctr_drop", seed=seed, campaign_id=campaign_id)
        try:
            dx = diagnose(days)
        except ValueError:
            continue
        if not dx.anomaly or dx.cause != "ctr":
            continue
        baseline = aggregate(days[:BASELINE_DAYS])
        current = aggregate(days[BASELINE_DAYS : BASELINE_DAYS + CURRENT_DAYS])
        if baseline_cpc_cvr(baseline, current) != "cpm":
            continue
        return {
            "campaign_id": campaign_id,
            "diagnosis": dx,
            "baseline": baseline,
            "current": current,
            "b1": "cpm",
        }
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score AdCopilot against dashboard baselines.")
    parser.add_argument("--n", type=int, default=100, help="campaigns per scenario (default 100)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--sigma", type=float, default=DEFAULT_NOISE_SIGMA)
    parser.add_argument("--sweeps", action="store_true", help="also run threshold, noise, and volume sweeps")
    args = parser.parse_args(argv)

    primary = evaluate(args.n, seed=args.seed, noise_sigma=args.sigma)
    _print_result(primary, "Primary evaluation")

    example = find_ctr_gap_example(seed=args.seed)
    if example is not None:
        dx = example["diagnosis"]
        b = example["baseline"]
        c = example["current"]
        print("Worked CTR-drop example (B1 says CPM, B2 says CTR)")
        print(f"  campaign_id={example['campaign_id']}")
        print(
            f"  CPA {b.cpa:.2f} -> {c.cpa:.2f} ({dx.cpa_change_pct:+.1f}%)  "
            f"cause={dx.cause}  shares={dx.shares}"
        )
        print(
            f"  CPM {b.cpm:.2f} -> {c.cpm:.2f}  CTR {b.ctr:.4f} -> {c.ctr:.4f}  "
            f"CVR {b.cvr:.4f} -> {c.cvr:.4f}  CPC {b.cpc:.2f} -> {c.cpc:.2f}"
        )
        print()

    if args.sweeps:
        print("Threshold sweep")
        for share, margin in ((70.0, 40.0), (55.0, 15.0), (60.0, 20.0), (75.0, 40.0)):
            result = evaluate(
                args.n,
                seed=args.seed,
                noise_sigma=args.sigma,
                high_share=share,
                high_margin=margin,
            )
            _print_result(result, f"share={share:g} margin={margin:g}")

        print("Noise sweep (B2 only)")
        for sigma in (0.06, 0.12, 0.20, 0.30, 0.45):
            result = evaluate(args.n, seed=args.seed, noise_sigma=sigma)
            row = result.systems["B2"]
            print(f"  sigma={sigma:.2f}  {_fmt(row)}")
        print()

        print("Volume sweep (B2 only)")
        for impressions in (300.0, 2_000.0, 6_000.0, 15_000.0):
            result = evaluate(args.n, seed=args.seed, noise_sigma=args.sigma, impressions=impressions)
            row = result.systems["B2"]
            print(f"  impr/day={impressions:.0f}  {_fmt(row)}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
