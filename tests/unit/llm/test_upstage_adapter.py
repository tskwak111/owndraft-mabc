"""Upstage adapter tests with the OpenAI SDK's real HTTP layer mocked via respx.

Covers the fixed retry policy: one transient retry (timeout/connection/429/5xx),
exactly one schema-correction request per call, and distinct error codes.
"""

import json

import httpx
import pytest
import respx
from owndraft.core.errors import GatewayError, ModelOutputError
from owndraft.core.settings import Settings
from owndraft.llm.upstage import UpstageModelGateway
from pydantic import BaseModel

pytestmark = pytest.mark.asyncio

CHAT_URL = "https://api.upstage.ai/v1/chat/completions"


class Probe(BaseModel):
    answer: int


def _json_response(raw_content: str) -> httpx.Response:
    body = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "solar-pro4",
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": raw_content}, "finish_reason": "stop"}
        ],
    }
    return httpx.Response(200, json=body)


def _gateway() -> UpstageModelGateway:
    settings = Settings(upstage_api_key="test-key")
    return UpstageModelGateway(settings)


async def test_success_parses_json_without_retries():
    with respx.mock(base_url="https://api.upstage.ai") as mock:
        route = mock.post("/v1/chat/completions").mock(return_value=_json_response('{"answer": 42}'))
        gateway = _gateway()

        result = await gateway.complete_json(
            operation="probe", system_prompt="s", user_prompt="u", response_model=Probe
        )

        assert result.answer == 42
        assert route.call_count == 1
        assert gateway.parse_retries_used == 0


async def test_schema_mismatch_triggers_single_correction_request():
    with respx.mock(base_url="https://api.upstage.ai") as mock:
        route = mock.post("/v1/chat/completions")
        route.side_effect = [
            _json_response('{"wrong_field": true}'),
            _json_response('{"answer": 7}'),
        ]
        gateway = _gateway()

        result = await gateway.complete_json(
            operation="probe", system_prompt="s", user_prompt="u", response_model=Probe
        )

        assert result.answer == 7
        assert route.call_count == 2
        assert gateway.parse_retries_used == 1
        correction = json.loads(route.calls[1].request.content)["messages"][-1]["content"]
        assert "스키마" in correction
        assert "answer" in correction


async def test_persistent_schema_violation_raises_after_correction():
    with respx.mock(base_url="https://api.upstage.ai") as mock:
        route = mock.post("/v1/chat/completions")
        route.side_effect = [
            _json_response('{"nope": 1}'),
            _json_response('{"still_wrong": 2}'),
        ]
        gateway = _gateway()

        with pytest.raises(ModelOutputError) as exc_info:
            await gateway.complete_json(
                operation="probe", system_prompt="s", user_prompt="u", response_model=Probe
            )

        assert exc_info.value.code == "model_schema_mismatch"
        # initial call + exactly one correction; never a third attempt
        assert route.call_count == 2


async def test_rate_limit_is_retried_once_then_succeeds():
    with respx.mock(base_url="https://api.upstage.ai") as mock:
        route = mock.post("/v1/chat/completions")
        rate_limited = httpx.Response(429, json={"error": "rate limited"})
        route.side_effect = [rate_limited, _json_response('{"answer": 5}')]
        gateway = _gateway()

        result = await gateway.complete_json(
            operation="probe", system_prompt="s", user_prompt="u", response_model=Probe
        )

        assert result.answer == 5
        assert route.call_count == 2


async def test_double_rate_limit_maps_to_gateway_error():
    with respx.mock(base_url="https://api.upstage.ai") as mock:
        route = mock.post("/v1/chat/completions")
        route.side_effect = [
            httpx.Response(429, json={"error": "rate limited"}),
            httpx.Response(429, json={"error": "rate limited"}),
        ]
        gateway = _gateway()

        with pytest.raises(GatewayError) as exc_info:
            await gateway.complete_json(
                operation="probe", system_prompt="s", user_prompt="u", response_model=Probe
            )

        assert exc_info.value.code == "gateway_rate_limited"
        assert route.call_count == 2


async def test_timeout_maps_to_gateway_timeout_code():
    with respx.mock(base_url="https://api.upstage.ai") as mock:
        # httpx-level timeout is translated to APITimeoutError by the OpenAI SDK
        mock.post("/v1/chat/completions").side_effect = httpx.ReadTimeout(
            "timed out", request=httpx.Request("POST", CHAT_URL)
        )
        gateway = _gateway()

        with pytest.raises(GatewayError) as exc_info:
            await gateway.complete_json(
                operation="probe", system_prompt="s", user_prompt="u", response_model=Probe
            )

        assert exc_info.value.code == "gateway_timeout"
