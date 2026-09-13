"""Evaluation harness: AdCopilot vs dashboard baseline, seeded replicates."""

from __future__ import annotations

from adcopilot.evaluate import evaluate
from adcopilot.generate import SCENARIOS


def test_evaluate_scores_adcopilot_and_dashboard_side_by_side() -> None:
    result = evaluate(n_per_class=6, seed=1)
    assert result.n == 6 * len(SCENARIOS)
    for system in ("B0", "B1", "B1b", "B2-", "B2"):
        row = result.systems[system]
        assert 0.0 <= row["overall_acc"] <= 1.0
        assert 0.0 <= row["coverage"] <= 1.0
        assert "selective_acc" in row
    assert result.systems["B2"]["tpr"] >= 0.0
    assert result.systems["B2"]["fpr"] >= 0.0


def test_evaluate_is_deterministic_for_a_seed() -> None:
    a = evaluate(n_per_class=4, seed=99)
    b = evaluate(n_per_class=4, seed=99)
    assert a.systems["B1"]["overall_acc"] == b.systems["B1"]["overall_acc"]
    assert a.systems["B2"]["overall_acc"] == b.systems["B2"]["overall_acc"]
    assert a.systems["B2"]["refusal_given_det"] == b.systems["B2"]["refusal_given_det"]
