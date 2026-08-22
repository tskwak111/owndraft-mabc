import pytest
from owndraft.contracts.stage1 import ContextQuestion
from owndraft.llm.gateway import FakeModelGateway
from pydantic import BaseModel

pytestmark = pytest.mark.asyncio


class QuestionBundle(BaseModel):
    questions: list[ContextQuestion]


async def test_fake_gateway_returns_operation_specific_fixture():
    gateway = FakeModelGateway({"context_gap": {"questions": []}})
    result = await gateway.complete_json(
        operation="context_gap",
        system_prompt="system",
        user_prompt="user",
        response_model=QuestionBundle,
    )
    assert result.questions == []
    assert gateway.calls[0].operation == "context_gap"


async def test_fake_gateway_records_call_metadata_without_raw_text():
    gateway = FakeModelGateway({"profile_voice": {"language": "ko"}})

    class Profile(BaseModel):
        language: str = "ko"

    await gateway.complete_json(
        operation="profile_voice",
        system_prompt="시스템 프롬프트 본문",
        user_prompt="사용자 프롬프트 본문",
        response_model=Profile,
    )

    call = gateway.calls[0]
    assert call.operation == "profile_voice"
    assert len(call.system_prompt_sha256) == 64
    assert len(call.user_prompt_sha256) == 64
    assert "시스템 프롬프트 본문" not in str(gateway.calls)


async def test_fake_gateway_queue_supports_sequential_responses():
    gateway = FakeModelGateway({})
    gateway.queue_response("critic_fact", {"critic": "fact", "score": 2.0})
    gateway.queue_response("critic_fact", {"critic": "fact", "score": 5.0})

    class Critic(BaseModel):
        critic: str
        score: float

    first = await gateway.complete_json(
        operation="critic_fact", system_prompt="", user_prompt="", response_model=Critic
    )
    second = await gateway.complete_json(
        operation="critic_fact", system_prompt="", user_prompt="", response_model=Critic
    )

    assert (first.score, second.score) == (2.0, 5.0)
    assert gateway.operations.count("critic_fact") == 2


async def test_fake_gateway_raises_when_no_fixture_configured():
    from owndraft.core.errors import ModelOutputError

    gateway = FakeModelGateway({})

    try:
        await gateway.complete_json(
            operation="unknown_op",
            system_prompt="",
            user_prompt="",
            response_model=QuestionBundle,
        )
    except ModelOutputError as error:
        assert "unknown_op" in str(error)
    else:
        raise AssertionError("ModelOutputError가 발생해야 한다")
