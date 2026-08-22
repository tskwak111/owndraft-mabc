"""Context question validation: reject vague, duplicated, or answered asks."""

import re

from pydantic import BaseModel

from owndraft.contracts.stage1 import ContextQuestion
from owndraft.text.normalization import normalize_for_comparison

_VAGUE_RE = re.compile(r"더 구체적으로|구체적으로 말해|어떤 느낌|더 알려|자세히 말해")
_PARTICLES = ("은", "는", "이", "가", "을", "를", "도", "에서", "으로", "로", "만", "까지")

_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "experience": ("경험", "사례", "직접", "겪은"),
    "number": ("얼마나", "몇", "수치", "시간", "금액", "퍼센트", "비용"),
    "opinion": ("생각", "의견", "입장", "느꼈"),
    "goal": ("바라", "해보길", "목표", "기대하"),
    "source": ("출처", "근거", "자료", "어디서"),
}

_RANK_BY_TYPE = {"source": 1, "experience": 2, "number": 3, "opinion": 4, "goal": 5}
_MAX_QUESTIONS = 3


class _Candidate(BaseModel):
    question: ContextQuestion
    rank: int
    index: int
    info_types: list[str]


def _content_chunks(question_text: str) -> list[str]:
    normalized = normalize_for_comparison(question_text)
    chunks: list[str] = []
    for raw in normalized.replace("?", "").replace(".", "").split(" "):
        core = raw.strip()
        for particle in _PARTICLES:
            if core.endswith(particle) and len(core) > len(particle):
                core = core[: -len(particle)]
                break
        if len(core) >= 2:
            chunks.append(core)
    return chunks


def _is_answered_in_original(question_text: str, original_text: str) -> bool:
    """A distinctive 3+ char chunk already present in the source means answered."""

    return any(
        len(chunk) >= 3 and chunk in original_text
        for chunk in _content_chunks(question_text)
    )


def _requested_info_types(question_text: str) -> list[str]:
    found = [
        answer_type
        for answer_type, keywords in _TYPE_KEYWORDS.items()
        if any(keyword in question_text for keyword in keywords)
    ]
    return found


def _reject_reasons(candidate: _Candidate, original_text: str) -> list[str]:
    reasons: list[str] = []
    text = candidate.question.question
    if _VAGUE_RE.search(text):
        reasons.append("vague_question")
    if len(candidate.info_types) > 1:
        reasons.append("multi_info_request")
    if _is_answered_in_original(text, original_text):
        reasons.append("already_answered")
    return reasons


def select_context_questions(
    candidates: list[ContextQuestion],
    original_text: str,
) -> list[ContextQuestion]:
    """Filter invalid candidates, dedupe by target_gap, cap at three.

    Ranking (fact/source → experience → measurable change → position → reader
    action) decides which questions survive when there are more than three;
    presentation order follows the original candidate order.
    """

    scored: list[_Candidate] = []
    for index, question in enumerate(candidates):
        info_types = _requested_info_types(question.question)
        scored.append(
            _Candidate(
                question=question,
                rank=_RANK_BY_TYPE.get(question.expected_answer_type, 9),
                index=index,
                info_types=info_types,
            )
        )

    seen_gaps: set[str] = set()
    valid: list[_Candidate] = []
    for candidate in scored:
        reasons = _reject_reasons(candidate, original_text)
        if reasons or candidate.question.target_gap in seen_gaps:
            continue
        seen_gaps.add(candidate.question.target_gap)
        valid.append(candidate)

    if len(valid) > _MAX_QUESTIONS:
        ranked = sorted(valid, key=lambda candidate: (candidate.rank, candidate.index))
        keep_ids = {candidate.question.id for candidate in ranked[:_MAX_QUESTIONS]}
    else:
        keep_ids = {candidate.question.id for candidate in valid}

    return [
        candidate.question
        for candidate in sorted(valid, key=lambda c: c.index)
        if candidate.question.id in keep_ids
    ]
