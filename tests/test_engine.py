"""Tests for metric identities, seeded diagnosis accuracy, and determinism."""

from __future__ import annotations

import json
import math

import pytest

from adcopilot.engine import diagnose
from adcopilot.explain import explain
from adcopilot.generate import SCENARIOS, expected_label, generate_campaign
from adcopilot.metrics import (
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


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_seeded_scenario_matches_ground_truth(scenario: str) -> None:
    expected = expected_label(scenario)
    result = diagnose(generate_campaign(scenario))
    assert result.anomaly is expected["anomaly"]
    assert result.cause == expected["cause"]
    assert result.confidence == expected["confidence"]


def test_refusal_on_ambiguous() -> None:
    result = diagnose(generate_campaign("ambiguous"))
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
    result = diagnose(generate_campaign("stable"))
    assert result.anomaly is False
    assert result.cause is None


def test_aggregate_matches_window_totals() -> None:
    days = generate_campaign("stable")
    period = aggregate(days[:14])
    assert period.impressions == sum(d.impressions for d in days[:14])
    assert math.isclose(period.cpa, period.cost / period.conversions)


def test_all_shock_accuracy_bar() -> None:
    shocks = [s for s in SCENARIOS if s != "stable"]
    correct = 0
    for scenario in shocks:
        expected = expected_label(scenario)
        result = diagnose(generate_campaign(scenario))
        if (
            result.anomaly is expected["anomaly"]
            and result.cause == expected["cause"]
            and result.confidence == expected["confidence"]
        ):
            correct += 1
    assert correct == len(shocks) == 5
