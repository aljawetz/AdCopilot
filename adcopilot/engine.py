"""Deterministic CPA anomaly detection, decomposition, and refusal logic."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from adcopilot.generate import BASELINE_DAYS, CURRENT_DAYS
from adcopilot.metrics import DailyMetrics, PeriodMetrics, aggregate

ANOMALY_CPA_RISE = 0.20  # flag when current CPA > baseline * 1.20
IMPRESSION_DROP_THRESHOLD = 0.15
HIGH_SHARE = 70.0
HIGH_MARGIN = 40.0


@dataclass(frozen=True)
class Diagnosis:
    anomaly: bool
    baseline_cpa: float
    current_cpa: float
    cpa_change_pct: float
    cause: str | None
    confidence: str | None
    shares: dict[str, float]
    baseline: dict[str, float]
    current: dict[str, float]
    next_step: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _period_snapshot(p: PeriodMetrics) -> dict[str, float]:
    return {
        "impressions": round(p.impressions, 6),
        "clicks": round(p.clicks, 6),
        "cost": round(p.cost, 6),
        "conversions": round(p.conversions, 6),
        "ctr": round(p.ctr, 8),
        "cvr": round(p.cvr, 8),
        "cpc": round(p.cpc, 8),
        "cpm": round(p.cpm, 8),
        "cpa": round(p.cpa, 8),
        "lost_is_budget": round(p.lost_is_budget, 8),
        "lost_is_rank": round(p.lost_is_rank, 8),
    }


def _log_delta(current: float, baseline: float) -> float:
    if current <= 0 or baseline <= 0:
        return 0.0
    return math.log(current) - math.log(baseline)


def _normalize_shares(raw: dict[str, float]) -> dict[str, float]:
    total = sum(abs(v) for v in raw.values())
    if total == 0:
        return {k: 0.0 for k in raw}
    return {k: round(100.0 * abs(v) / total, 4) for k, v in raw.items()}


def _leading_with_margin(shares: dict[str, float]) -> tuple[str | None, float, float]:
    ordered = sorted(shares.items(), key=lambda kv: kv[1], reverse=True)
    if not ordered:
        return None, 0.0, 0.0
    leader, lead_share = ordered[0]
    second = ordered[1][1] if len(ordered) > 1 else 0.0
    return leader, lead_share, lead_share - second


def _decompose_rate_drivers(baseline: PeriodMetrics, current: PeriodMetrics) -> dict[str, float]:
    """Leaf shares of Δlog(CPA) across CPM, CTR, and CVR.

    Identity: CPA = CPM / (1000 * CTR * CVR)
    so Δln(CPA) = Δln(CPM) − Δln(CTR) − Δln(CVR).
    """
    raw = {
        "cpm": _log_delta(current.cpm, baseline.cpm),
        "ctr": -_log_delta(current.ctr, baseline.ctr),
        "cvr": -_log_delta(current.cvr, baseline.cvr),
    }
    return _normalize_shares(raw)


def _decompose_cpc_cvr(baseline: PeriodMetrics, current: PeriodMetrics) -> dict[str, float]:
    raw = {
        "cpc": _log_delta(current.cpc, baseline.cpc),
        "cvr": -_log_delta(current.cvr, baseline.cvr),
    }
    return _normalize_shares(raw)


def _visibility_cause(
    baseline: PeriodMetrics,
    current: PeriodMetrics,
) -> tuple[str | None, dict[str, float]]:
    if baseline.impressions <= 0:
        return None, {}
    drop = 1.0 - (current.impressions / baseline.impressions)
    if drop < IMPRESSION_DROP_THRESHOLD:
        return None, {}

    d_budget = current.lost_is_budget - baseline.lost_is_budget
    d_rank = current.lost_is_rank - baseline.lost_is_rank
    if d_budget <= 0 and d_rank <= 0:
        return None, {}

    shares = _normalize_shares({"budget": max(d_budget, 0.0), "rank": max(d_rank, 0.0)})
    leader, lead_share, margin = _leading_with_margin(shares)
    if leader is None:
        return None, shares
    if lead_share >= HIGH_SHARE and margin >= HIGH_MARGIN:
        return leader, shares
    return "ambiguous", shares


def _next_step(cause: str | None) -> str | None:
    steps = {
        "cpm": "Review Auction Insights and competitor pressure before raising bids.",
        "ctr": "Inspect ad creative and query match quality; CTR decline raised CPC.",
        "cvr": "Check landing page, offer, and conversion tracking before changing bids.",
        "cpc": "Decompose CPC into CPM vs CTR; do not raise budget until the driver is clear.",
        "budget": "Raise daily budget or reallocate spend; Search Lost IS (budget) rose.",
        "rank": "Improve Ad Rank (bid, Quality Score, assets); Search Lost IS (rank) rose.",
        "ambiguous": "Do not act on a single lever; investigate mixed cost and conversion signals.",
    }
    return steps.get(cause) if cause else None


def diagnose(days: Sequence[DailyMetrics]) -> Diagnosis:
    """Run the full deterministic pipeline on a daily series.

    Expects at least BASELINE_DAYS + CURRENT_DAYS rows in chronological order.
    Identical input yields identical Diagnosis.to_dict() output.
    """
    if len(days) < BASELINE_DAYS + CURRENT_DAYS:
        raise ValueError(
            f"Need at least {BASELINE_DAYS + CURRENT_DAYS} days; got {len(days)}"
        )

    baseline_days = days[:BASELINE_DAYS]
    current_days = days[BASELINE_DAYS : BASELINE_DAYS + CURRENT_DAYS]
    baseline = aggregate(baseline_days)
    current = aggregate(current_days)

    if baseline.cpa <= 0:
        raise ValueError("Baseline CPA is undefined (no conversions in baseline window)")

    cpa_change_pct = (current.cpa - baseline.cpa) / baseline.cpa
    anomaly = cpa_change_pct > ANOMALY_CPA_RISE

    if not anomaly:
        return Diagnosis(
            anomaly=False,
            baseline_cpa=round(baseline.cpa, 8),
            current_cpa=round(current.cpa, 8),
            cpa_change_pct=round(cpa_change_pct * 100.0, 4),
            cause=None,
            confidence=None,
            shares={},
            baseline=_period_snapshot(baseline),
            current=_period_snapshot(current),
            next_step=None,
        )

    vis_cause, vis_shares = _visibility_cause(baseline, current)
    if vis_cause is not None:
        cause = vis_cause
        shares = vis_shares
        if cause == "ambiguous":
            confidence = "low"
        else:
            confidence = "high"
        return Diagnosis(
            anomaly=True,
            baseline_cpa=round(baseline.cpa, 8),
            current_cpa=round(current.cpa, 8),
            cpa_change_pct=round(cpa_change_pct * 100.0, 4),
            cause=cause,
            confidence=confidence,
            shares=shares,
            baseline=_period_snapshot(baseline),
            current=_period_snapshot(current),
            next_step=_next_step(cause),
        )

    leaf = _decompose_rate_drivers(baseline, current)
    cpc_cvr = _decompose_cpc_cvr(baseline, current)
    shares = {
        **leaf,
        "cpc": cpc_cvr.get("cpc", 0.0),
        "cvr_vs_cpc": cpc_cvr.get("cvr", 0.0),
    }

    # Primary cause is the leading leaf driver among cpm/ctr/cvr.
    leaf_only = {k: leaf[k] for k in ("cpm", "ctr", "cvr")}
    leader, lead_share, margin = _leading_with_margin(leaf_only)
    if leader is not None and lead_share >= HIGH_SHARE and margin >= HIGH_MARGIN:
        cause = leader
        confidence = "high"
    else:
        cause = "ambiguous"
        confidence = "low"

    return Diagnosis(
        anomaly=True,
        baseline_cpa=round(baseline.cpa, 8),
        current_cpa=round(current.cpa, 8),
        cpa_change_pct=round(cpa_change_pct * 100.0, 4),
        cause=cause,
        confidence=confidence,
        shares={k: round(v, 4) for k, v in shares.items()},
        baseline=_period_snapshot(baseline),
        current=_period_snapshot(current),
        next_step=_next_step(cause),
    )
