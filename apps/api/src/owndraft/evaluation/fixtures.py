"""Loading and validation of evaluation case fixtures."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from owndraft.contracts.stage1 import EditMode, Stage1Request
from owndraft.core.errors import ContractError


class CaseRequest(BaseModel):
    text: str
    purpose: str
    audience: str
    edit_mode: EditMode = EditMode.VOICE
    voice_samples: list[str] = Field(default_factory=list, max_length=3)
    locked_phrases: list[str] = Field(default_factory=list, max_length=50)


class CaseLabels(BaseModel):
    locked_values: list[str]
    expected_pattern_codes: list[str]
    forbidden_new_claims: list[str]
    required_meaning: list[str]
    allowed_edit_summary: str


class EvaluationCase(BaseModel):
    id: str
    category: str
    request: CaseRequest
    context_answers: dict[str, str] = Field(default_factory=dict)
    labels: CaseLabels

    @property
    def locked_values(self) -> list[str]:
        return self.labels.locked_values

    @property
    def expected_pattern_codes(self) -> list[str]:
        return self.labels.expected_pattern_codes

    @property
    def forbidden_new_claims(self) -> list[str]:
        return self.labels.forbidden_new_claims

    @property
    def allowed_edit_summary(self) -> str:
        return self.labels.allowed_edit_summary

    def to_stage1_request(self) -> Stage1Request:
        return Stage1Request(
            text=self.request.text,
            purpose=self.request.purpose,
            audience=self.request.audience,
            edit_mode=self.request.edit_mode,
            voice_samples=self.request.voice_samples,
            locked_phrases=self.request.locked_phrases,
        )


def load_cases(cases_dir: Path) -> list[EvaluationCase]:
    """Load all YAML case files deterministically ordered by filename."""

    directory = Path(cases_dir)
    if not directory.is_dir():
        raise ContractError(
            "evaluation_cases_missing",
            detail=f"평가 케이스 디렉터리가 없습니다: {directory}",
        )
    cases: list[EvaluationCase] = []
    for path in sorted(directory.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            cases.append(EvaluationCase.model_validate(raw))
        except Exception as error:
            raise ContractError(
                "evaluation_case_invalid",
                detail=f"케이스 파일 검증 실패({path.name}): {error}",
            ) from error
    return cases
