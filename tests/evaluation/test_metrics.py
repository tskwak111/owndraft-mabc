import pytest
from owndraft.evaluation.metrics import EvaluationResult, aggregate_results


def test_case_fails_even_with_high_semantic_score_when_number_changes():
    result = EvaluationResult(
        locked_fact_preservation=0.8,
        new_claim_rate=0.0,
        semantic_fidelity=5.0,
        pattern_reduction=0.8,
        voice_constraint_match=0.95,
    )

    assert result.passed is False


def test_perfect_case_passes():
    result = EvaluationResult(
        locked_fact_preservation=1.0,
        new_claim_rate=0.0,
        semantic_fidelity=5.0,
        pattern_reduction=1.0,
        voice_constraint_match=1.0,
    )

    assert result.passed is True


def test_new_claim_rate_above_zero_fails_case():
    result = EvaluationResult(
        locked_fact_preservation=1.0,
        new_claim_rate=0.5,
        semantic_fidelity=5.0,
        pattern_reduction=1.0,
        voice_constraint_match=1.0,
    )

    assert result.passed is False


def test_aggregate_averages_are_computed_over_cases():
    first = EvaluationResult(
        locked_fact_preservation=1.0,
        new_claim_rate=0.0,
        semantic_fidelity=5.0,
        pattern_reduction=0.8,
        voice_constraint_match=None,
    )
    second = EvaluationResult(
        locked_fact_preservation=1.0,
        new_claim_rate=0.0,
        semantic_fidelity=4.0,
        pattern_reduction=0.6,
        voice_constraint_match=1.0,
    )
    summary = aggregate_results([first, second])

    assert summary["average_pattern_reduction"] == pytest.approx(0.7)
    assert summary["average_semantic_fidelity"] == pytest.approx(4.5)
    assert summary["voice_mode_average_constraint_match"] == pytest.approx(1.0)
