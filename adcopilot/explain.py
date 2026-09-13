"""Template explanations filled only from structured Diagnosis fields."""

from __future__ import annotations

from adcopilot.engine import Diagnosis


def _pct(rate: float) -> str:
    return f"{rate * 100:.2f}%"


def _money(value: float) -> str:
    return f"${value:.2f}"


def explain(diagnosis: Diagnosis) -> str:
    """Plain-language, numbers-cited explanation. Never invents a cause."""
    b = diagnosis.baseline
    c = diagnosis.current

    if not diagnosis.anomaly:
        return (
            f"No abnormal CPA movement. Baseline CPA {_money(diagnosis.baseline_cpa)} "
            f"vs current {_money(diagnosis.current_cpa)} "
            f"({diagnosis.cpa_change_pct:+.1f}%), below the +20% anomaly threshold."
        )

    header = (
        f"CPA rose {diagnosis.cpa_change_pct:+.1f}% "
        f"({_money(diagnosis.baseline_cpa)} → {_money(diagnosis.current_cpa)})."
    )

    if diagnosis.cause == "ambiguous":
        share_bits = ", ".join(f"{k.upper()} {v:.0f}%" for k, v in sorted(diagnosis.shares.items()))
        body = (
            f"No single driver dominates ({share_bits}). "
            f"Confidence: Low. Refusal: do not name one root cause."
        )
        if diagnosis.next_step:
            body += f" Next: {diagnosis.next_step}"
        return f"{header} {body}"

    cause = diagnosis.cause or "unknown"
    conf = (diagnosis.confidence or "low").capitalize()

    if cause in ("budget", "rank"):
        label = "Search Lost IS (budget)" if cause == "budget" else "Search Lost IS (rank)"
        body = (
            f"Impressions fell "
            f"{b['impressions']:.0f} → {c['impressions']:.0f}. "
            f"{label} rose "
            f"{_pct(b['lost_is_budget'] if cause == 'budget' else b['lost_is_rank'])} → "
            f"{_pct(c['lost_is_budget'] if cause == 'budget' else c['lost_is_rank'])}. "
            f"Diagnosis: {cause}-capped visibility. Confidence: {conf}."
        )
    elif cause == "cpm":
        body = (
            f"CPM drove the change "
            f"({_money(b['cpm'])} → {_money(c['cpm'])}; share {diagnosis.shares.get('cpm', 0):.0f}%). "
            f"CTR {_pct(b['ctr'])} → {_pct(c['ctr'])}, "
            f"CVR {_pct(b['cvr'])} → {_pct(c['cvr'])}. "
            f"Diagnosis: auction price pressure. Confidence: {conf}."
        )
    elif cause == "cvr":
        body = (
            f"CVR drove the change "
            f"({_pct(b['cvr'])} → {_pct(c['cvr'])}; share {diagnosis.shares.get('cvr', 0):.0f}%). "
            f"CPC held near {_money(b['cpc'])} → {_money(c['cpc'])}. "
            f"Diagnosis: conversion-quality issue. Confidence: {conf}."
        )
    elif cause == "ctr":
        body = (
            f"CTR drove the change "
            f"({_pct(b['ctr'])} → {_pct(c['ctr'])}; share {diagnosis.shares.get('ctr', 0):.0f}%). "
            f"CPM {_money(b['cpm'])} → {_money(c['cpm'])}. "
            f"Diagnosis: engagement drop raising CPC. Confidence: {conf}."
        )
    else:
        body = f"Diagnosis: {cause}. Confidence: {conf}."

    if diagnosis.next_step:
        body += f" Next: {diagnosis.next_step}"
    return f"{header} {body}"
