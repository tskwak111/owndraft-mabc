import os

import pytest
from owndraft.core.settings import Settings
from owndraft.llm.upstage import UpstageModelGateway
from pydantic import BaseModel

pytestmark = [
    pytest.mark.skipif(not os.getenv("UPSTAGE_API_KEY"), reason="requires UPSTAGE_API_KEY"),
    pytest.mark.asyncio,
]


class SmokeResponse(BaseModel):
    operation: str
    safe: bool


async def test_real_upstage_returns_valid_json():
    gateway = UpstageModelGateway(Settings())
    result = await gateway.complete_json(
        operation="integration_smoke",
        system_prompt="Return valid JSON only.",
        user_prompt='Return {"operation":"integration_smoke","safe":true}.',
        response_model=SmokeResponse,
    )
    assert result == SmokeResponse(operation="integration_smoke", safe=True)
