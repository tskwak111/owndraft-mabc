import pytest

from tests.unit.workflow.conftest import QUESTION_FIXTURE, REQUEST_WITH_ABSTRACT_CLAIM

pytestmark = pytest.mark.asyncio


async def test_workflow_stops_before_rewrite_when_context_is_needed(workflow, fake_gateway):
    fake_gateway.set_response("find_context_gaps", {"questions": [QUESTION_FIXTURE]})

    result = await workflow.run(REQUEST_WITH_ABSTRACT_CLAIM)

    assert result.status == "needs_context"
    assert len(result.questions) == 1
    assert result.rewritten_text is None
    assert "write_candidate" not in fake_gateway.operations
    assert "repair_candidate" not in fake_gateway.operations


async def test_workflow_proceeds_when_no_questions_selected(workflow, fake_gateway):
    fake_gateway.set_response("find_context_gaps", {"questions": []})

    result = await workflow.run(REQUEST_WITH_ABSTRACT_CLAIM)

    assert result.status in {"completed", "blocked"}
    assert "write_candidate" in fake_gateway.operations


async def test_workflow_skips_questions_when_answers_supplied(workflow, fake_gateway):
    fake_gateway.set_response("find_context_gaps", {"questions": [QUESTION_FIXTURE]})

    result = await workflow.run(
        REQUEST_WITH_ABSTRACT_CLAIM, context_answers={"q_metric": "40분에서 5분"}
    )

    assert result.status != "needs_context"
    assert "write_candidate" in fake_gateway.operations
