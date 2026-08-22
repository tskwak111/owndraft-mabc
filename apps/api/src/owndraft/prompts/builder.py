"""Prompt builder for the fixed stage 1 model operations.

Every prompt carries only the minimum fields needed for its operation plus a
JSON schema. Prompts explicitly forbid new facts, detector-evasion goals, and
over-copying of user samples.
"""

import json
from typing import Any

from pydantic import BaseModel

from owndraft.contracts.stage1 import (
    CandidateDraft,
    ClaimBundle,
    CriticScore,
    PatternBundle,
    QuestionBundle,
    RewritePlan,
    VoiceProfile,
)

OPERATIONS: tuple[str, ...] = (
    "extract_claims",
    "scan_patterns",
    "profile_voice",
    "find_context_gaps",
    "plan_rewrite",
    "write_candidate",
    "critic_fact",
    "critic_fidelity",
    "critic_voice",
    "critic_naturalness",
    "repair_candidate",
)

_RESPONSE_MODELS: dict[str, type[BaseModel]] = {
    "extract_claims": ClaimBundle,
    "scan_patterns": PatternBundle,
    "profile_voice": VoiceProfile,
    "find_context_gaps": QuestionBundle,
    "plan_rewrite": RewritePlan,
    "write_candidate": CandidateDraft,
    "critic_fact": CriticScore,
    "critic_fidelity": CriticScore,
    "critic_voice": CriticScore,
    "critic_naturalness": CriticScore,
    "repair_candidate": CandidateDraft,
}

_GLOBAL_RULES_KO = (
    "공통 규칙:\n"
    "- 원문이나 사용자 답변에 없는 사실·통계·출처·경험·인용을 만들지 않는다.\n"
    "- AI 탐지 점수, 워터마크 제거, 탐지기 통과를 목표로 삼지 않는다.\n"
    "- 사용자 문체 샘플의 단어를 그대로 복제하거나 반복하지 않는다.\n"
    "- 지시한 JSON 스키마 외의 내용을 출력하지 않는다."
)


class OperationPrompt(BaseModel):
    operation: str
    system_prompt: str
    user_prompt: str
    response_model_name: str


def response_model_for(operation: str) -> type[BaseModel]:
    if operation not in _RESPONSE_MODELS:
        raise ValueError(f"알 수 없는 operation입니다: {operation}")
    return _RESPONSE_MODELS[operation]


def build_operation_prompt(
    operation: str,
    *,
    payload: dict[str, Any],
) -> OperationPrompt:
    """Build (system, user) prompts for one fixed operation.

    `payload` must contain only the fields that operation needs; it is embedded
    as compact JSON in the user prompt together with the response schema.
    """

    if operation not in _RESPONSE_MODELS:
        raise ValueError(f"알 수 없는 operation입니다: {operation}")
    model = _RESPONSE_MODELS[operation]
    schema_json = json.dumps(
        model.model_json_schema(), ensure_ascii=False, separators=(",", ":")
    )
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    system_prompt = (
        f"너는 OwnDraft 스킬의 '{operation}' 역할을 수행한다.\n"
        f"{_GLOBAL_RULES_KO}\n"
        f"출력 형식: {model.__name__} JSON 스키마와 동일한 단일 JSON 객체."
    )
    user_prompt = (
        f"operation: {operation}\n"
        f"입력(JSON): {payload_json}\n"
        f"응답 JSON 스키마: {schema_json}"
    )
    return OperationPrompt(
        operation=operation,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model_name=model.__name__,
    )


def schema_for(operation: str) -> dict[str, Any]:
    return _RESPONSE_MODELS[operation].model_json_schema()
