"""Seeded synthetic Google Ads-shaped campaigns with labeled shocks."""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Iterator

from adcopilot.metrics import DailyMetrics

BASELINE_DAYS = 14
CURRENT_DAYS = 7
TOTAL_DAYS = BASELINE_DAYS + CURRENT_DAYS
START_DATE = date(2026, 8, 1)
DEFAULT_SEED = 20260911
DEFAULT_NOISE_SIGMA = 0.08

SCENARIOS = (
    "cpm_spike",
    "ctr_drop",
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


def _rng_for(*parts: object) -> random.Random:
    digest = hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _lognormal_factor(rng: random.Random, sigma: float) -> float:
    if sigma <= 0:
        return 1.0
    return math.exp(rng.gauss(0.0, sigma))


def _binomial(rng: random.Random, n: int, p: float) -> int:
    """Integer count. Uses Random.binomialvariate when present (3.12+)."""
    if n <= 0 or p <= 0:
        return 0
    if p >= 1:
        return n
    binomialvariate = getattr(rng, "binomialvariate", None)
    if binomialvariate is not None:
        return int(binomialvariate(n, p))
    mean = n * p
    var = n * p * (1.0 - p)
    if var >= 9:
        draw = rng.gauss(mean, math.sqrt(var))
        return int(min(n, max(0, round(draw))))
    return sum(1 for _ in range(n) if rng.random() < p)


def _from_params(day: date, p: DayParams, rng: random.Random, noise_sigma: float) -> DailyMetrics:
    impressions = max(1, int(round(p.impressions * _lognormal_factor(rng, noise_sigma))))
    ctr = _clamp(p.ctr * _lognormal_factor(rng, noise_sigma), 0.001, 0.5)
    cvr = _clamp(p.cvr * _lognormal_factor(rng, noise_sigma), 0.001, 0.5)
    cpm = max(0.01, p.cpm * _lognormal_factor(rng, noise_sigma))
    lost_scale = 0.0 if noise_sigma <= 0 else min(0.03, noise_sigma * 0.25)
    lost_is_budget = _clamp(p.lost_is_budget + rng.gauss(0.0, lost_scale), 0.0, 0.9)
    lost_is_rank = _clamp(p.lost_is_rank + rng.gauss(0.0, lost_scale), 0.0, 0.9)

    clicks = _binomial(rng, impressions, ctr)
    conversions = _binomial(rng, clicks, cvr)
    cost = (cpm / 1000.0) * impressions
    return DailyMetrics(
        date=day.isoformat(),
        impressions=float(impressions),
        clicks=float(clicks),
        cost=cost,
        conversions=float(conversions),
        lost_is_budget=lost_is_budget,
        lost_is_rank=lost_is_rank,
    )


def _shock_cpm(baseline: DayParams) -> DayParams:
    return DayParams(
        impressions=baseline.impressions,
        ctr=baseline.ctr,
        cvr=baseline.cvr,
        cpm=baseline.cpm * 2.0,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=baseline.lost_is_rank,
    )


def _shock_ctr(baseline: DayParams) -> DayParams:
    return DayParams(
        impressions=baseline.impressions,
        ctr=baseline.ctr * 0.5,
        cvr=baseline.cvr,
        cpm=baseline.cpm,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=baseline.lost_is_rank,
    )


def _shock_cvr(baseline: DayParams) -> DayParams:
    return DayParams(
        impressions=baseline.impressions,
        ctr=baseline.ctr,
        cvr=baseline.cvr * 0.5,
        cpm=baseline.cpm,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=baseline.lost_is_rank,
    )


def _shock_budget(baseline: DayParams) -> DayParams:
    # Throttled delivery: leftover auctions are pricier. Do not plant a CVR drop.
    return DayParams(
        impressions=baseline.impressions * 0.80,
        ctr=baseline.ctr,
        cvr=baseline.cvr,
        cpm=baseline.cpm * 1.40,
        lost_is_budget=0.45,
        lost_is_rank=baseline.lost_is_rank,
    )


def _shock_rank(baseline: DayParams) -> DayParams:
    # Lost top slots cut CTR. Do not plant a CVR drop.
    return DayParams(
        impressions=baseline.impressions * 0.80,
        ctr=baseline.ctr * 0.70,
        cvr=baseline.cvr,
        cpm=baseline.cpm,
        lost_is_budget=baseline.lost_is_budget,
        lost_is_rank=0.50,
    )


def _shock_ambiguous(baseline: DayParams) -> DayParams:
    # CPM and CVR both move; neither leaf should dominate the 70/40 gate.
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
    "ctr_drop": _shock_ctr,
    "cvr_drop": _shock_cvr,
    "budget_capped": _shock_budget,
    "rank_capped": _shock_rank,
    "ambiguous": _shock_ambiguous,
    "stable": None,
}


def _draw_base_params(rng: random.Random, impressions: float | None) -> DayParams:
    base = _stable_params()
    mean_impr = impressions if impressions is not None else base.impressions * _lognormal_factor(rng, 0.20)
    return DayParams(
        impressions=max(500.0, mean_impr),
        ctr=_clamp(base.ctr * _lognormal_factor(rng, 0.12), 0.015, 0.15),
        cvr=_clamp(base.cvr * _lognormal_factor(rng, 0.12), 0.015, 0.15),
        cpm=max(3.0, base.cpm * _lognormal_factor(rng, 0.15)),
        lost_is_budget=_clamp(base.lost_is_budget + rng.uniform(-0.03, 0.03), 0.02, 0.30),
        lost_is_rank=_clamp(base.lost_is_rank + rng.uniform(-0.03, 0.03), 0.02, 0.40),
    )


def generate_campaign(
    scenario: str,
    *,
    seed: int = DEFAULT_SEED,
    campaign_id: int = 0,
    noise_sigma: float = DEFAULT_NOISE_SIGMA,
    impressions: float | None = None,
) -> list[DailyMetrics]:
    """Return 21 daily rows: 14 baseline + 7 current.

    Counts are integer draws (binomial clicks and conversions). Rate noise is
    lognormal. Identical (scenario, seed, campaign_id, noise_sigma, impressions)
    always yield identical series.
    """
    if scenario not in _SHOCKS:
        raise ValueError(f"Unknown scenario {scenario!r}; choose from {SCENARIOS}")

    param_rng = _rng_for(seed, scenario, campaign_id, "params")
    baseline = _draw_base_params(param_rng, impressions)
    shock_fn = _SHOCKS[scenario]
    current = shock_fn(baseline) if shock_fn else baseline

    days: list[DailyMetrics] = []
    for i in range(TOTAL_DAYS):
        day = START_DATE + timedelta(days=i)
        params = current if i >= BASELINE_DAYS else baseline
        day_rng = _rng_for(seed, scenario, campaign_id, i)
        days.append(_from_params(day, params, day_rng, noise_sigma))
    return days


def generate_dataset(
    n_per_class: int,
    *,
    seed: int = DEFAULT_SEED,
    noise_sigma: float = DEFAULT_NOISE_SIGMA,
    impressions: float | None = None,
) -> Iterator[tuple[str, int, list[DailyMetrics]]]:
    """Yield (scenario, campaign_id, days) for an evaluation replicate."""
    for scenario in SCENARIOS:
        for campaign_id in range(n_per_class):
            days = generate_campaign(
                scenario,
                seed=seed,
                campaign_id=campaign_id,
                noise_sigma=noise_sigma,
                impressions=impressions,
            )
            yield scenario, campaign_id, days


def expected_label(scenario: str) -> dict[str, object]:
    """Ground-truth evaluation labels for seeded scenarios."""
    labels: dict[str, dict[str, object]] = {
        "cpm_spike": {"anomaly": True, "cause": "cpm", "confidence": "high"},
        "ctr_drop": {"anomaly": True, "cause": "ctr", "confidence": "high"},
        "cvr_drop": {"anomaly": True, "cause": "cvr", "confidence": "high"},
        "budget_capped": {"anomaly": True, "cause": "budget", "confidence": "high"},
        "rank_capped": {"anomaly": True, "cause": "rank", "confidence": "high"},
        "ambiguous": {"anomaly": True, "cause": "ambiguous", "confidence": "low"},
        "stable": {"anomaly": False, "cause": None, "confidence": None},
    }
    if scenario not in labels:
        raise ValueError(f"Unknown scenario {scenario!r}")
    return labels[scenario]
