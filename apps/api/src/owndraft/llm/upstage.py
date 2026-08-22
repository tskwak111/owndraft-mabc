"""Upstage OpenAI-compatible gateway with bounded retries."""

from typing import TypeVar

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from owndraft.core.errors import GatewayError, ModelOutputError
from owndraft.core.settings import Settings
from owndraft.llm.parser import parse_model_json

T = TypeVar("T", bound=BaseModel)

_TRANSIENT_RETRIES = 1


def _json_schema_hint(response_model: type[BaseModel]) -> str:
    import json

    return json.dumps(
        response_model.model_json_schema(), ensure_ascii=False, separators=(",", ":")
    )


class UpstageModelGateway:
    """Calls an Upstage-compatible chat endpoint and enforces JSON contracts.

    Retry policy is fixed:
    - transient transport/server failures: at most one identical retry
    - schema validation failures: at most one correction prompt that carries
      only the validation error and JSON schema (never the original document)
    """

    def __init__(self, settings: Settings) -> None:
        # Retry policy is owned by this gateway (exactly one transient retry),
        # so the SDK's built-in retries are disabled explicitly.
        self._client = AsyncOpenAI(
            api_key=settings.upstage_api_key.get_secret_value(),
            base_url=settings.upstage_base_url,
            max_retries=0,
        )
        self._model = settings.upstage_chat_model
        self.parse_retries_used = 0

    async def _request(
        self, *, messages: list[ChatCompletionMessageParam]
    ) -> str:
        last_error: GatewayError | None = None
        for attempt in range(_TRANSIENT_RETRIES + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    temperature=0.2,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content or ""
            except APITimeoutError as error:
                last_error = GatewayError("gateway_timeout", detail="모델 응답 시간 초과")
                if attempt == 0:
                    continue
                raise last_error from error
            except APIConnectionError as error:
                last_error = GatewayError("gateway_connection_error", detail="모델 연결 실패")
                if attempt == 0:
                    continue
                raise last_error from error
            except RateLimitError as error:
                last_error = GatewayError("gateway_rate_limited", detail="요청 한도 초과")
                if attempt == 0:
                    continue
                raise last_error from error
            except InternalServerError as error:
                last_error = GatewayError("gateway_server_error", detail="모델 서버 오류")
                if attempt == 0:
                    continue
                raise last_error from error
        raise last_error or GatewayError("gateway_error", detail="알 수 없는 게이트웨이 오류")

    async def complete_json(
        self,
        *,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """One schema-correction request per call, never per-instance budget."""

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = await self._request(messages=messages)
        try:
            return parse_model_json(raw, response_model)
        except ModelOutputError as error:
            if error.code != "model_schema_mismatch":
                raise

            correction_messages: list[ChatCompletionMessageParam] = [
                *messages,
                {
                    "role": "user",
                    "content": (
                        "이전 응답이 스키마를 위반했습니다. 오류와 JSON 스키마만 확인하고 "
                        "스키마에 맞는 JSON만 다시 출력하세요. 원문을 반복하지 마세요.\n"
                        f"검증 오류: {error.detail}\n"
                        f"JSON 스키마: {_json_schema_hint(response_model)}"
                    ),
                },
            ]
            self.parse_retries_used += 1
            raw_retry = await self._request(messages=correction_messages)
            return parse_model_json(raw_retry, response_model)
