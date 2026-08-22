import pytest

from tests.unit.workflow.conftest import (
    CANDIDATE_WITH_WRONG_30_MINUTES,
    CORRECTED_40_TO_5_MINUTES,
    FAILED_FACT_CRITIC,
    PASSED_FACT_CRITIC,
    VALID_REQUEST,
)

pytestmark = pytest.mark.asyncio


async def test_workflow_repairs_once_when_fact_critic_fails(workflow, fake_gateway):
    fake_gateway.queue_response("write_candidate", CANDIDATE_WITH_WRONG_30_MINUTES)
    fake_gateway.queue_response("critic_fact", FAILED_FACT_CRITIC)
    fake_gateway.queue_response("repair_candidate", CORRECTED_40_TO_5_MINUTES)
    fake_gateway.queue_response("critic_fact", PASSED_FACT_CRITIC)

    result = await workflow.run(VALID_REQUEST, context_answers={"q1": "40분에서 5분"})

    assert result.status == "completed"
    assert fake_gateway.operations.count("repair_candidate") == 1
    assert result.preservation is not None
    assert result.preservation.repair_attempts == 1
    assert result.rewritten_text is not None
    assert "40분" in result.rewritten_text


async def test_workflow_blocks_after_second_preservation_failure(workflow, fake_gateway):
    fake_gateway.queue_response("write_candidate", CANDIDATE_WITH_WRONG_30_MINUTES)
    fake_gateway.queue_response("critic_fact", FAILED_FACT_CRITIC)
    fake_gateway.queue_response("repair_candidate", CANDIDATE_WITH_WRONG_30_MINUTES)
    fake_gateway.queue_response("critic_fact", FAILED_FACT_CRITIC)

    result = await workflow.run(
        VALID_REQUEST,
        context_answers={"q1": "회의록 정리가 40분에서 5분으로 줄었다."},
    )

    assert result.status == "blocked"
    assert result.rewritten_text is None
    assert result.preservation is not None
    assert result.preservation.passed is False
    assert fake_gateway.operations.count("repair_candidate") == 1


async def test_repair_prompt_receives_only_machine_readable_issues(workflow, fake_gateway):
    fake_gateway.queue_response("write_candidate", CANDIDATE_WITH_WRONG_30_MINUTES)
    fake_gateway.queue_response("critic_fact", FAILED_FACT_CRITIC)
    fake_gateway.queue_response("repair_candidate", CORRECTED_40_TO_5_MINUTES)
    fake_gateway.queue_response("critic_fact", PASSED_FACT_CRITIC)

    await workflow.run(VALID_REQUEST, context_answers={"q1": "40분에서 5분"})

    repair_calls = [
        call for call in fake_gateway.calls if call.operation == "repair_candidate"
    ]
    assert repair_calls, "repair 호출이 기록되어야 한다"


async def test_workflow_records_trace_events_without_sensitive_text(workflow):
    await workflow.run(VALID_REQUEST, context_answers={"q1": "40분에서 5분"})

    events = workflow.last_trace_events
    states = [event.state.value for event in events]

    assert "deterministic_claims" in states
    assert "acceptance_gate" in states
    serialized = repr(events)
    assert "Solar" not in serialized
    assert "https://example.com" not in serialized
