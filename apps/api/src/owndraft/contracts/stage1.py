"""Stage 1 input/output and domain contracts.

These types are the fixed contract for every stage 1 task. Changing them
requires updating this module first, then the contract tests, then usages.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high"]
FindingAction = Literal["keep", "rewrite", "delete", "ask"]
VoiceConfidence = Literal["none", "low", "medium", "high"]
AnswerType = Literal["experience", "number", "opinion", "goal", "source"]


class EditMode(StrEnum):
    MINIMAL = "minimal"
    VOICE = "voice"


class Claim(BaseModel):
    id: str
    claim_type: str
    source_text: str
    normalized_value: str
    start: int
    end: int
    locked: bool = True
    evidence_type: str


class PatternFinding(BaseModel):
    span_id: str
    pattern_code: str
    severity: Severity
    reason: str
    action: FindingAction


class Formality(BaseModel):
    level: Literal["casual", "polite", "formal"] = "polite"
    honorific: bool = True


class SentenceStyle(BaseModel):
    average_length: Literal["short", "medium", "long"] = "medium"
    variance: Literal["low", "medium", "high"] = "medium"
    preferred_opening: str | None = None


class ParagraphStyle(BaseModel):
    average_sentences: int = Field(default=3, ge=1, le=20)
    spacing: Literal["frequent", "occasional", "rare"] = "occasional"


class ReasoningStyle(BaseModel):
    order: list[str] = Field(default_factory=list, max_length=5)
    uncertainty_style: list[str] = Field(default_factory=list, max_length=10)


class PunctuationStyle(BaseModel):
    comma_frequency: Literal["low", "medium", "high"] = "medium"
    parentheses_frequency: Literal["low", "medium", "high"] = "low"
    em_dash: Literal["avoid", "sometimes", "often"] = "avoid"


class Lexicon(BaseModel):
    preferred: list[str] = Field(default_factory=list, max_length=10)
    avoided: list[str] = Field(default_factory=list, max_length=10)


class Rhetoric(BaseModel):
    list_preference: Literal["mechanical_triples", "flexible", "avoids_lists"] = "flexible"
    metaphor_frequency: Literal["low", "medium", "high"] = "low"
    humor_style: Literal["none", "dry", "playful"] = "none"


class VoiceProfile(BaseModel):
    """Structured voice profile derived from user samples.

    `lexicon.preferred`/`avoided` are capped at 10 items and verbatim entries
    longer than 30 characters are rejected to prevent over-copying samples.
    """

    language: str = "ko"
    formality: Formality = Formality()
    sentence: SentenceStyle = SentenceStyle()
    paragraph: ParagraphStyle = ParagraphStyle()
    reasoning: ReasoningStyle = ReasoningStyle()
    punctuation: PunctuationStyle = PunctuationStyle()
    lexicon: Lexicon = Lexicon()
    rhetoric: Rhetoric = Rhetoric()
    confidence: VoiceConfidence = "low"
    sample_chars: int = Field(ge=0)
    source: Literal["model", "heuristic", "user_edited"] = "model"

    def model_post_init(self, __context: object, /) -> None:
        too_long = [
            phrase
            for phrase in [*self.lexicon.preferred, *self.lexicon.avoided]
            if len(phrase) > 30
        ]
        if too_long:
            raise ValueError(
                f"voice profile lexicon phrases must be at most 30 characters: {too_long[:3]}"
            )


class ContextQuestion(BaseModel):
    id: str
    question: str
    target_gap: str
    expected_answer_type: AnswerType


class ChangeReason(BaseModel):
    span_id: str | None = None
    change_type: str
    reason: str


class PreservationIssue(BaseModel):
    code: str
    severity: Severity
    claim_id: str | None = None
    detail: str = ""


class PreservationReport(BaseModel):
    passed: bool
    issues: list[PreservationIssue] = Field(default_factory=list)
    locked_total: int = 0
    preserved_locked: int = 0
    new_claim_count: int = 0
    repair_attempts: int = 0

    @property
    def high_severity_issue_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "high")


class CriticScore(BaseModel):
    """Shared result shape for fact/fidelity/voice/naturalness critics."""

    critic: str
    score: float = Field(ge=0, le=5)
    passed: bool = False
    skipped: bool = False
    new_claim_count: int = 0
    severe_error_count: int = 0
    high_severity_unresolved: int = 0
    constraint_match: float | None = Field(default=None, ge=0, le=1)
    issues: list[str] = Field(default_factory=list)


class Stage1Request(BaseModel):
    text: str = Field(min_length=20, max_length=10_000)
    purpose: str = Field(min_length=2, max_length=300)
    audience: str = Field(min_length=2, max_length=300)
    edit_mode: EditMode = EditMode.VOICE
    voice_samples: list[str] = Field(default_factory=list, max_length=3)
    locked_phrases: list[str] = Field(default_factory=list, max_length=50)

    @property
    def voice_sample_chars(self) -> int:
        return sum(len(sample.strip()) for sample in self.voice_samples)

    @property
    def voice_sample_confidence(self) -> VoiceConfidence:
        chars = self.voice_sample_chars
        if chars < 80:
            return "none"
        if chars < 160:
            return "low"
        if chars < 400:
            return "medium"
        return "high"

    @property
    def effective_edit_mode(self) -> EditMode:
        if self.edit_mode is EditMode.VOICE and self.voice_sample_chars < 80:
            return EditMode.MINIMAL
        return self.edit_mode


class Stage1Result(BaseModel):
    status: Literal["needs_context", "completed", "blocked"]
    diagnosis: list[PatternFinding] = Field(default_factory=list)
    questions: list[ContextQuestion] = Field(default_factory=list)
    rewritten_text: str | None = None
    changes: list[ChangeReason] = Field(default_factory=list)
    preservation: PreservationReport | None = None
    trace_id: str


class ClaimBundle(BaseModel):
    """Response contract for the extract_claims operation."""

    claims: list[Claim] = Field(default_factory=list)


class PatternBundle(BaseModel):
    """Response contract for the scan_patterns operation."""

    findings: list[PatternFinding] = Field(default_factory=list)


class QuestionBundle(BaseModel):
    """Response contract for the find_context_gaps operation."""

    questions: list[ContextQuestion] = Field(default_factory=list)


class PlanOperation(BaseModel):
    span_id: str | None = None
    action: Literal[
        "keep", "delete", "condense", "rewrite", "insert_user_answer", "reorder"
    ]
    note_ko: str = ""


class RewritePlan(BaseModel):
    """Response contract for the plan_rewrite operation."""

    goals: list[str] = Field(default_factory=list, max_length=10)
    operations: list[PlanOperation] = Field(default_factory=list)


class CandidateDraft(BaseModel):
    """Response contract for write_candidate / repair_candidate operations."""

    rewritten_text: str
    change_reasons: list[ChangeReason] = Field(default_factory=list)
