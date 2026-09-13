"""Deterministic synthetic Google Ads-shaped campaign series with labeled shocks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

from adcopilot.metrics import DailyMetrics

BASELINE_DAYS = 14
CURRENT_DAYS = 7
TOTAL_DAYS = BASELINE_DAYS + CURRENT_DAYS
START_DATE = date(2026, 8, 1)

SCENARIOS = (
    "cpm_spike",
    "cvr_drop",
    "budget_capped",
    "rank_capped",
    "ambiguous",
    "stable",
)


@dataclass(frozen=True)
class DayParams:
    impressions: float
    ctr: float
    cvr: float
    cpm: float
    lost_is_budget: float
    lost_is_rank: float


def _stable_params() -> DayParams:
    return DayParams(
        impressions=10_000.0,
        ctr=0.05,
        cvr=0.04,
        cpm=12.0,
        lost_is_budget=0.10,
        lost_is_rank=0.15,
    )


def _from_params(day: date, p: DayParams) -> DailyMetrics:
    impressions = p.impressions
    clicks = impressions * p.ctr
    cost = (p.cpm / 1000.0) * impressions
    conversions = clicks * p.cvr
    return DailyMetrics(
        date=day.isoformat(),
        impressions=impressions,
        clicks=clicks,
        cost=cost,
        conversions=conversions,
        lost_is_budget=p.lost_is_budget,
        lost_is_rank=p.lost_is_rank,
    )


def _shock_cpm(baseline: DayParams) -> DayParams:
    # ~2x CPM → CPA doubles via CPC; CTR/CVR unchanged.
    return DayParams(
        impressions=baseline.impressions,
        ctr=baseline.ctr,
        cvr=baseline.cvr,
        cpm=baseline.cpm * 2.0,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=baseline.lost_is_rank,
    )


def _shock_cvr(baseline: DayParams) -> DayParams:
    # CVR halves → CPA doubles; cost rates unchanged.
    return DayParams(
        impressions=baseline.impressions,
        ctr=baseline.ctr,
        cvr=baseline.cvr * 0.5,
        cpm=baseline.cpm,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=baseline.lost_is_rank,
    )


def _shock_budget(baseline: DayParams) -> DayParams:
    # Impressions cut by budget cap; Lost IS (budget) dominates.
    return DayParams(
        impressions=baseline.impressions * 0.55,
        ctr=baseline.ctr,
        cvr=baseline.cvr * 0.72,  # thinner leftover traffic; CPA rises
        cpm=baseline.cpm,
        lost_is_budget=0.45,
        lost_is_rank=baseline.lost_is_rank,
    )


def _shock_rank(baseline: DayParams) -> DayParams:
    return DayParams(
        impressions=baseline.impressions * 0.55,
        ctr=baseline.ctr * 0.95,
        cvr=baseline.cvr * 0.72,
        cpm=baseline.cpm * 1.05,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=0.50,
    )


def _shock_ambiguous(baseline: DayParams) -> DayParams:
    # CPM and CVR both move enough that neither leaf share dominates.
    return DayParams(
        impressions=baseline.impressions,
        ctr=baseline.ctr,
        cvr=baseline.cvr * 0.72,
        cpm=baseline.cpm * 1.45,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=baseline.lost_is_rank,
    )


_SHOCKS: dict[str, Callable[[DayParams], DayParams] | None] = {
    "cpm_spike": _shock_cpm,
    "cvr_drop": _shock_cvr,
    "budget_capped": _shock_budget,
    "rank_capped": _shock_rank,
    "ambiguous": _shock_ambiguous,
    "stable": None,
}


def generate_campaign(scenario: str) -> list[DailyMetrics]:
    """Return 21 deterministic daily rows: 14 baseline + 7 current.

    The shock (if any) applies only to the current window. Identical
    scenario names always yield identical series.
    """
    if scenario not in _SHOCKS:
        raise ValueError(f"Unknown scenario {scenario!r}; choose from {SCENARIOS}")

    baseline = _stable_params()
    shock_fn = _SHOCKS[scenario]
    current = shock_fn(baseline) if shock_fn else baseline

    days: list[DailyMetrics] = []
    for i in range(TOTAL_DAYS):
        day = START_DATE + timedelta(days=i)
        params = current if i >= BASELINE_DAYS else baseline
        days.append(_from_params(day, params))
    return days


def expected_label(scenario: str) -> dict[str, object]:
    """Ground-truth evaluation labels for seeded scenarios."""
    labels: dict[str, dict[str, object]] = {
        "cpm_spike": {"anomaly": True, "cause": "cpm", "confidence": "high"},
        "cvr_drop": {"anomaly": True, "cause": "cvr", "confidence": "high"},
        "budget_capped": {"anomaly": True, "cause": "budget", "confidence": "high"},
        "rank_capped": {"anomaly": True, "cause": "rank", "confidence": "high"},
        "ambiguous": {"anomaly": True, "cause": "ambiguous", "confidence": "low"},
        "stable": {"anomaly": False, "cause": None, "confidence": None},
    }
    if scenario not in labels:
        raise ValueError(f"Unknown scenario {scenario!r}")
    return labels[scenario]
