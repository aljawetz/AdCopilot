"""Generator contract: binomial counts, seeded replicates, visibility without CVR."""

from __future__ import annotations

import math

from adcopilot.generate import (
    SCENARIOS,
    _shock_budget,
    _shock_rank,
    _stable_params,
    expected_label,
    generate_campaign,
)
from adcopilot.metrics import aggregate


def test_clicks_and_conversions_are_integer_counts() -> None:
    days = generate_campaign("stable", seed=11, campaign_id=0)
    for day in days:
        assert day.impressions == int(day.impressions)
        assert day.clicks == int(day.clicks)
        assert day.conversions == int(day.conversions)
        assert 0 <= day.clicks <= day.impressions
        assert 0 <= day.conversions <= day.clicks


def test_same_seed_and_campaign_id_are_identical() -> None:
    a = generate_campaign("cvr_drop", seed=7, campaign_id=3)
    b = generate_campaign("cvr_drop", seed=7, campaign_id=3)
    assert [d.clicks for d in a] == [d.clicks for d in b]
    assert [d.cost for d in a] == [d.cost for d in b]


def test_different_campaign_ids_are_not_identical() -> None:
    a = generate_campaign("stable", seed=7, campaign_id=0)
    b = generate_campaign("stable", seed=7, campaign_id=1)
    assert [d.clicks for d in a] != [d.clicks for d in b]


def test_ctr_drop_is_a_labeled_scenario() -> None:
    assert "ctr_drop" in SCENARIOS
    assert expected_label("ctr_drop") == {
        "anomaly": True,
        "cause": "ctr",
        "confidence": "high",
    }


def test_rank_shock_does_not_plant_a_cvr_move() -> None:
    baseline = _stable_params()
    shocked = _shock_rank(baseline)
    assert shocked.cvr == baseline.cvr
    assert shocked.impressions < baseline.impressions
    assert shocked.lost_is_rank > baseline.lost_is_rank


def test_budget_shock_does_not_plant_a_cvr_move() -> None:
    baseline = _stable_params()
    shocked = _shock_budget(baseline)
    assert shocked.cvr == baseline.cvr
    assert shocked.impressions < baseline.impressions
    assert shocked.lost_is_budget > baseline.lost_is_budget


def test_rank_capped_window_cvr_stays_near_baseline() -> None:
    days = generate_campaign(
        "rank_capped", seed=1, campaign_id=0, noise_sigma=0.0, impressions=20_000
    )
    before = aggregate(days[:14])
    after = aggregate(days[14:])
    assert math.isclose(after.cvr, before.cvr, rel_tol=0.15)
