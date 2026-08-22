"""Model gateway protocol plus deterministic fake for tests and CI."""

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from owndraft.core.errors import ModelOutputError

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class GatewayCall:
    operation: str
    system_prompt_sha256: str
    user_prompt_sha256: str
    response_model: str
    parse_retried: bool = False


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ModelGateway(Protocol):
    async def complete_json(
        self,
        *,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T: ...


class FakeModelGateway:
    """Deterministic fake gateway; never logs or returns raw prompt text."""

    def __init__(self, fixtures: dict[str, dict[str, Any]]) -> None:
        self._fixtures = {operation: [payload] for operation, payload in fixtures.items()}
        self._queues: dict[str, list[dict[str, Any]]] = {}
        self.calls: list[GatewayCall] = []

    @property
    def operations(self) -> list[str]:
        return [call.operation for call in self.calls]

    def set_response(self, operation: str, payload: dict[str, Any]) -> None:
        self._fixtures[operation] = [payload]

    def queue_response(self, operation: str, payload: dict[str, Any]) -> None:
        self._queues.setdefault(operation, []).append(payload)

    def _next_payload(self, operation: str) -> dict[str, Any]:
        queue = self._queues.get(operation)
        if queue:
            return queue.pop(0)
        fixtures = self._fixtures.get(operation)
        if fixtures:
            return fixtures[0]
        raise ModelOutputError(
            "model_output_unparseable",
            detail=f"FakeModelGateway에 '{operation}' 응답이 설정되지 않았습니다.",
        )

    async def complete_json(
        self,
        *,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        payload = self._next_payload(operation)
        try:
            result = response_model.model_validate(payload)
        except ValidationError as error:
            raise ModelOutputError(
                "model_schema_mismatch",
                detail=f"'{operation}' fixture가 스키마와 일치하지 않습니다.",
            ) from error
        self.calls.append(
            GatewayCall(
                operation=operation,
                system_prompt_sha256=_digest(system_prompt),
                user_prompt_sha256=_digest(user_prompt),
                response_model=response_model.__name__,
            )
        )
        return result
