"""Structured output parsing: extract and validate model JSON."""

import json
import re

from pydantic import BaseModel, ValidationError

from owndraft.core.errors import ModelOutputError

_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL)
_OBJECT_RE = re.compile(r"\{.*\}|\[.*\]", re.DOTALL)


def _extract_json_text(raw: str) -> str | None:
    fence_match = _FENCE_RE.search(raw)
    if fence_match:
        candidate = fence_match.group(1).strip()
        if candidate:
            return candidate
    object_match = _OBJECT_RE.search(raw)
    if object_match:
        return object_match.group()
    return None


def parse_model_json[T: BaseModel](raw: str, response_model: type[T]) -> T:
    """Parse raw model output into `response_model`.

    Local parsing is a single attempt with no retry; the caller (gateway)
    decides whether to send one schema-correction request.
    """

    if not raw.strip():
        raise ModelOutputError(
            "model_output_unparseable",
            detail="모델 출력이 비어 있어 JSON을 만들 수 없습니다.",
        )

    json_text = _extract_json_text(raw)
    if json_text is None:
        raise ModelOutputError(
            "model_output_unparseable",
            detail="모델 출력에서 JSON 객체를 찾지 못했습니다.",
        )
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ModelOutputError(
            "model_output_unparseable",
            detail=f"JSON 파싱에 실패했습니다: {error.msg}",
        ) from error

    try:
        return response_model.model_validate(data)
    except ValidationError as error:
        first = error.errors()[0]
        location = ".".join(str(part) for part in first.get("loc", ()))
        raise ModelOutputError(
            "model_schema_mismatch",
            detail=f"스키마 검증 실패({location}): {first.get('msg', '')}",
        ) from error
