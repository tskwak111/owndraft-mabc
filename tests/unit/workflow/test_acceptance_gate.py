
from owndraft.contracts.stage1 import CriticScore, PreservationReport
from owndraft.workflow.gates import (
    CriticBundle,
    collect_machine_readable_issues,
    decide_acceptance,
)

PASSED_REPORT = PreservationReport(passed=True, locked_total=3, preserved_locked=3)


def _bundle(
    fact: CriticScore | None = None,
    fidelity: CriticScore | None = None,
    voice: CriticScore | None = None,
    naturalness: CriticScore | None = None,
) -> CriticBundle:
    return CriticBundle(
        fact=fact or CriticScore(critic="fact", score=5.0, passed=True),
        fidelity=fidelity or CriticScore(critic="fidelity", score=5.0, passed=True),
        voice=voice or CriticScore(critic="voice", score=0, skipped=True),
        naturalness=naturalness or CriticScore(critic="naturalness", score=5.0, passed=True),
    )


def test_gate_passes_with_clean_report_and_critics():
    decision = decide_acceptance(PASSED_REPORT, _bundle())

    assert decision.passed is True
    assert decision.repair_instructions == []


def test_gate_fails_when_deterministic_report_fails():
    report = PreservationReport(
        passed=False,
        locked_total=3,
        preserved_locked=2,
        issues=[{"code": "locked_value_missing", "severity": "high"}],
    )

    decision = decide_acceptance(report, _bundle())

    assert decision.passed is False
    assert any(issue.code == "locked_value_missing" for issue in decision.repair_instructions)


def test_gate_fails_on_fact_critic_new_claims():
    fact = CriticScore(critic="fact", score=2.0, new_claim_count=1)

    decision = decide_acceptance(PASSED_REPORT, _bundle(fact=fact))

    assert decision.passed is False


def test_gate_fails_on_severe_fidelity_errors():
    fidelity = CriticScore(critic="fidelity", score=1.0, severe_error_count=1)

    decision = decide_acceptance(PASSED_REPORT, _bundle(fidelity=fidelity))

    assert decision.passed is False


def test_gate_fails_on_high_severity_unresolved_naturalness():
    naturalness = CriticScore(critic="naturalness", score=3.0, high_severity_unresolved=2)

    decision = decide_acceptance(PASSED_REPORT, _bundle(naturalness=naturalness))

    assert decision.passed is False


def test_gate_requires_voice_constraint_match_when_not_skipped():
    weak_voice = CriticScore(critic="voice", score=3.0, constraint_match=0.75)
    strong_voice = CriticScore(critic="voice", score=5.0, constraint_match=0.92)

    assert decide_acceptance(PASSED_REPORT, _bundle(voice=weak_voice)).passed is False
    assert decide_acceptance(PASSED_REPORT, _bundle(voice=strong_voice)).passed is True


def test_collect_machine_readable_issues_spans_report_and_critics():
    report = PreservationReport(
        passed=False,
        issues=[
            {"code": "polarity_changed", "severity": "high", "claim_id": "clm_0004"},
        ],
    )
    fidelity = CriticScore(critic="fidelity", score=2.0, issues=["핵심 주장 반전"])

    instructions = collect_machine_readable_issues(report, _bundle(fidelity=fidelity))

    codes = {instruction.code for instruction in instructions}
    assert "polarity_changed" in codes
    assert any("핵심 주장 반전" in instruction.detail for instruction in instructions)
