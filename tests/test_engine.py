"""Tests for metric identities, seeded diagnosis accuracy, and determinism."""

from __future__ import annotations

import json
import math

import pytest

from datetime import date, timedelta

from adcopilot.engine import baseline_biggest_mover, baseline_cpc_cvr, diagnose
from adcopilot.explain import explain
from adcopilot.generate import generate_campaign
from adcopilot.metrics import (
    DailyMetrics,
    PeriodMetrics,
    aggregate,
    cpa_from_cpc_cvr,
    cpc_from_cpm_ctr,
    derive_rates,
)


def test_metric_identities_hold_on_derived_rates() -> None:
    impressions, clicks, cost, conversions = 10_000.0, 500.0, 120.0, 20.0
    ctr, cvr, cpc, cpm, cpa = derive_rates(impressions, clicks, cost, conversions)
    assert math.isclose(ctr, 0.05)
    assert math.isclose(cvr, 0.04)
    assert math.isclose(cpc, 0.24)
    assert math.isclose(cpm, 12.0)
    assert math.isclose(cpa, 6.0)
    assert math.isclose(cpc_from_cpm_ctr(cpm, ctr), cpc)
    assert math.isclose(cpa_from_cpc_cvr(cpc, cvr), cpa)


def test_generate_campaign_length_and_determinism() -> None:
    a = generate_campaign("cvr_drop")
    b = generate_campaign("cvr_drop")
    assert len(a) == 21
    assert [d.date for d in a] == [d.date for d in b]
    assert [d.cost for d in a] == [d.cost for d in b]


def test_day_to_day_noise_is_present_but_deterministic() -> None:
    days = generate_campaign("stable")
    costs = [d.cost for d in days]
    assert len(set(round(c, 6) for c in costs)) > 1
    assert generate_campaign("stable")[3].impressions == days[3].impressions


def _day(offset: int, row: dict[str, float]) -> DailyMetrics:
    return DailyMetrics(
        date=(date(2026, 8, 1) + timedelta(days=offset)).isoformat(),
        impressions=row["impressions"],
        clicks=row["clicks"],
        cost=row["cost"],
        conversions=row["conversions"],
        lost_is_budget=row["lost_is_budget"],
        lost_is_rank=row["lost_is_rank"],
    )


def _constant_campaign(baseline: dict[str, float], current: dict[str, float]) -> list[DailyMetrics]:
    return [_day(i, baseline) for i in range(14)] + [_day(14 + i, current) for i in range(7)]


_BASE = {
    "impressions": 10_000.0,
    "clicks": 500.0,
    "cost": 120.0,
    "conversions": 20.0,
    "lost_is_budget": 0.10,
    "lost_is_rank": 0.15,
}


@pytest.mark.parametrize(
    "name,current,cause,confidence",
    [
        (
            "cpm_spike",
            {**_BASE, "cost": 240.0},
            "cpm",
            "high",
        ),
        (
            "ctr_drop",
            {**_BASE, "clicks": 250.0, "conversions": 10.0},
            "ctr",
            "high",
        ),
        (
            "cvr_drop",
            {**_BASE, "conversions": 10.0},
            "cvr",
            "high",
        ),
        (
            "budget_capped",
            {
                **_BASE,
                "impressions": 8_000.0,
                "clicks": 400.0,
                "cost": 134.4,
                "conversions": 16.0,
                "lost_is_budget": 0.45,
            },
            "budget",
            "high",
        ),
        (
            "rank_capped",
            {
                **_BASE,
                "impressions": 8_000.0,
                "clicks": 280.0,
                "cost": 96.0,
                "conversions": 11.2,
                "lost_is_rank": 0.50,
            },
            "rank",
            "high",
        ),
        (
            "ambiguous",
            {**_BASE, "cost": 174.0, "conversions": 14.4},
            "ambiguous",
            "low",
        ),
    ],
)
def test_noiseless_shock_matches_planted_cause(
    name: str,
    current: dict[str, float],
    cause: str,
    confidence: str,
) -> None:
    result = diagnose(_constant_campaign(_BASE, current))
    assert result.anomaly is True
    assert result.cause == cause
    assert result.confidence == confidence


def test_refusal_on_ambiguous() -> None:
    current = {**_BASE, "cost": 174.0, "conversions": 14.4}
    result = diagnose(_constant_campaign(_BASE, current))
    assert result.anomaly is True
    assert result.cause == "ambiguous"
    assert result.confidence == "low"
    text = explain(result)
    assert "Refusal" in text or "refuse" in text.lower() or "do not name" in text.lower()


def test_identical_input_identical_json() -> None:
    days = generate_campaign("cpm_spike")
    first = json.dumps(diagnose(days).to_dict(), sort_keys=True, separators=(",", ":"))
    second = json.dumps(diagnose(days).to_dict(), sort_keys=True, separators=(",", ":"))
    assert first == second


def test_stable_not_flagged() -> None:
    result = diagnose(_constant_campaign(_BASE, _BASE))
    assert result.anomaly is False
    assert result.cause is None


def test_aggregate_matches_window_totals() -> None:
    days = generate_campaign("stable")
    period = aggregate(days[:14])
    assert period.impressions == sum(d.impressions for d in days[:14])
    assert math.isclose(period.cpa, period.cost / period.conversions)


def _period(
    impressions: float,
    clicks: float,
    cost: float,
    conversions: float,
) -> PeriodMetrics:
    ctr, cvr, cpc, cpm, cpa = derive_rates(impressions, clicks, cost, conversions)
    return PeriodMetrics(
        impressions=impressions,
        clicks=clicks,
        cost=cost,
        conversions=conversions,
        lost_is_budget=0.1,
        lost_is_rank=0.15,
        ctr=ctr,
        cvr=cvr,
        cpc=cpc,
        cpm=cpm,
        cpa=cpa,
    )


def test_dashboard_baseline_blames_cpm_when_cpc_rises() -> None:
    """Google Ads headline: CPC up reads as a cost problem."""
    baseline = _period(10_000, 500, 120.0, 20.0)
    # CPM doubled, CTR/CVR fixed → CPC doubles.
    current = _period(10_000, 500, 240.0, 20.0)
    assert baseline_cpc_cvr(baseline, current) == "cpm"


def test_dashboard_baseline_blames_cvr_when_cvr_falls() -> None:
    baseline = _period(10_000, 500, 120.0, 20.0)
    current = _period(10_000, 500, 120.0, 10.0)
    assert baseline_cpc_cvr(baseline, current) == "cvr"


def test_dashboard_baseline_cannot_see_ctr_collapse() -> None:
    """CTR collapse inflates CPC; the dashboard rival calls that a cost problem."""
    baseline = _period(10_000, 500, 120.0, 20.0)
    # Same CPM and CVR, half the clicks → CPC doubles, CPA doubles.
    current = _period(10_000, 250, 120.0, 10.0)
    assert baseline_cpc_cvr(baseline, current) == "cpm"
    assert baseline_biggest_mover(baseline, current) == "ctr"
