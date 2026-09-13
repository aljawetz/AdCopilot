"""Metric identities and period aggregation for Google Ads-shaped daily rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DailyMetrics:
    """One day of campaign reporting fields (synthetic or real-shaped)."""

    date: str
    impressions: float
    clicks: float
    cost: float
    conversions: float
    lost_is_budget: float  # Search Lost IS (budget), fraction 0–1
    lost_is_rank: float  # Search Lost IS (rank), fraction 0–1


@dataclass(frozen=True)
class PeriodMetrics:
    """Totals and derived rates for a multi-day window."""

    impressions: float
    clicks: float
    cost: float
    conversions: float
    lost_is_budget: float
    lost_is_rank: float
    ctr: float
    cvr: float
    cpc: float
    cpm: float
    cpa: float


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def derive_rates(
    impressions: float,
    clicks: float,
    cost: float,
    conversions: float,
) -> tuple[float, float, float, float, float]:
    """Return CTR, CVR, CPC, CPM, CPA from totals."""
    ctr = safe_div(clicks, impressions)
    cvr = safe_div(conversions, clicks)
    cpc = safe_div(cost, clicks)
    cpm = safe_div(cost, impressions) * 1000.0
    cpa = safe_div(cost, conversions)
    return ctr, cvr, cpc, cpm, cpa


def cpc_from_cpm_ctr(cpm: float, ctr: float) -> float:
    """Identity: CPC = (CPM / 1000) / CTR."""
    return safe_div(cpm / 1000.0, ctr)


def cpa_from_cpc_cvr(cpc: float, cvr: float) -> float:
    """Identity: CPA = CPC / CVR."""
    return safe_div(cpc, cvr)


def aggregate(days: Sequence[DailyMetrics]) -> PeriodMetrics:
    """Sum raw columns over a window, then derive rates. Lost IS is impression-weighted."""
    if not days:
        raise ValueError("Cannot aggregate an empty day window")

    impressions = sum(d.impressions for d in days)
    clicks = sum(d.clicks for d in days)
    cost = sum(d.cost for d in days)
    conversions = sum(d.conversions for d in days)

    if impressions > 0:
        lost_is_budget = sum(d.lost_is_budget * d.impressions for d in days) / impressions
        lost_is_rank = sum(d.lost_is_rank * d.impressions for d in days) / impressions
    else:
        lost_is_budget = 0.0
        lost_is_rank = 0.0

    ctr, cvr, cpc, cpm, cpa = derive_rates(impressions, clicks, cost, conversions)
    return PeriodMetrics(
        impressions=impressions,
        clicks=clicks,
        cost=cost,
        conversions=conversions,
        lost_is_budget=lost_is_budget,
        lost_is_rank=lost_is_rank,
        ctr=ctr,
        cvr=cvr,
        cpc=cpc,
        cpm=cpm,
        cpa=cpa,
    )
