"""Voice profiling: heuristic fallback and model-profile validation."""

import re
from collections import Counter
from typing import Literal

from pydantic import ValidationError

from owndraft.contracts.stage1 import (
    Formality,
    Lexicon,
    ParagraphStyle,
    PunctuationStyle,
    SentenceStyle,
    VoiceConfidence,
    VoiceProfile,
)
from owndraft.core.errors import ContractError

FormalityLevel = Literal["casual", "polite", "formal"]
FrequencyLevel = Literal["low", "medium", "high"]
LengthBucket = Literal["short", "medium", "long"]

_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+|\n+")
_TOKEN_RE = re.compile(r"[가-힣]{2,5}")


def sample_chars_of(samples: list[str]) -> int:
    return sum(len(sample.strip()) for sample in samples)


def confidence_for(sample_chars: int) -> VoiceConfidence:
    if sample_chars < 80:
        return "none"
    if sample_chars < 160:
        return "low"
    if sample_chars < 400:
        return "medium"
    return "high"


def _sentence_texts(samples: list[str]) -> list[str]:
    sentences: list[str] = []
    for sample in samples:
        for part in _SENTENCE_SPLIT_RE.split(sample):
            if part.strip():
                sentences.append(part.strip())
    return sentences or [""]


def _length_bucket(average: float) -> LengthBucket:
    if average <= 20:
        return "short"
    if average <= 50:
        return "medium"
    return "long"


def _variance_bucket(values: list[int], average: float) -> Literal["low", "medium", "high"]:
    if len(values) < 2:
        return "low"
    variance = sum((value - average) ** 2 for value in values) / len(values)
    deviation = variance**0.5
    ratio = deviation / average if average else 0.0
    if ratio < 0.25:
        return "low"
    if ratio < 0.5:
        return "medium"
    return "high"


def _frequency_bucket(per_sentence: float, low: float, high: float) -> FrequencyLevel:
    if per_sentence < low:
        return "low"
    if per_sentence < high:
        return "medium"
    return "high"


def _formality(sentences: list[str]) -> tuple[FormalityLevel, bool]:
    polite = sum(
        1 for sentence in sentences if sentence.endswith(("요", "습니다", "니다", "세요"))
    )
    casual = sum(1 for sentence in sentences if sentence.endswith("다"))
    total = max(1, polite + casual)
    honorific = polite >= casual and polite > 0
    ratio = polite / total
    level: FormalityLevel
    if (not honorific and ratio < 0.1) or ratio < 0.3:
        level = "casual"
    elif ratio < 0.8:
        level = "polite"
    else:
        level = "formal"
    return level, honorific


def _repeated_tokens(samples: list[str]) -> list[str]:
    tokens: Counter[str] = Counter()
    for sample in samples:
        tokens.update(_TOKEN_RE.findall(sample))
    repeated = [token for token, count in tokens.items() if count >= 2]
    repeated.sort(key=lambda token: (-tokens[token], token))
    return repeated[:5]


def fallback_voice_profile(samples: list[str]) -> VoiceProfile:
    """Heuristic-only profile used when no model call is available.

    It infers only surface statistics and must never claim deep voice
    similarity; `source="heuristic"` marks that explicitly.
    """

    chars = sample_chars_of(samples)
    sentences = _sentence_texts(samples)
    lengths = [len(sentence) for sentence in sentences]
    average_length = sum(lengths) / max(1, len(lengths))

    paragraphs = [
        paragraph.strip() for paragraph in "\n".join(samples).split("\n") if paragraph.strip()
    ] or [" ".join(sentences)]
    paragraph_counts = [
        max(1, len([part for part in _SENTENCE_SPLIT_RE.split(paragraph) if part.strip()]))
        for paragraph in paragraphs
    ]
    average_paragraph_sentences = sum(paragraph_counts) / max(1, len(paragraph_counts))
    commas = sum(sentence.count(",") + sentence.count("、") for sentence in sentences)
    parens = sum(sentence.count("(") for sentence in sentences)

    level, honorific = _formality(sentences)

    return VoiceProfile(
        language="ko",
        formality=Formality(level=level, honorific=honorific),
        sentence=SentenceStyle(
            average_length=_length_bucket(average_length),  # type: ignore[arg-type]
            variance=_variance_bucket(lengths, average_length),  # type: ignore[arg-type]
        ),
        paragraph=ParagraphStyle(
            average_sentences=round(min(max(average_paragraph_sentences, 1), 20)),
            spacing="frequent" if len(paragraphs) > 2 else "occasional",
        ),
        punctuation=PunctuationStyle(
            comma_frequency=_frequency_bucket(commas / max(1, len(sentences)), 0.4, 1.0),
            parentheses_frequency=_frequency_bucket(parens / max(1, len(sentences)), 0.1, 0.4),
            em_dash="avoid",
        ),
        lexicon=Lexicon(preferred=_repeated_tokens(samples), avoided=[]),
        confidence=confidence_for(chars),
        sample_chars=chars,
        source="heuristic",
    )


def build_voice_profile_prompt(samples: list[str], purpose: str = "") -> str:
    """Build the user prompt for the profile_voice operation.

    The prompt states the anti-overcopy rule so the model profiles structure
    instead of parroting sample wording.
    """

    joined = "\n---\n".join(sample.strip() for sample in samples if sample.strip())
    chars = sample_chars_of(samples)
    return (
        "아래 사용자 문체 샘플을 분석해 구조화된 문체 프로필(JSON)로 만들어 주세요.\n"
        f"목적: {purpose or '미지정'}\n"
        f"샘플 개수: {len(samples)} / 총 글자 수: {chars}\n"
        "규칙: 샘플의 단어나 문장을 그대로 복제하거나 반복하지 않는다.\n"
        "30자가 넘는 표현을 프로필에 담지 않는다. 확신도는 샘플 길이에 맞춰 보수적으로 둔다.\n\n"
        f"샘플:\n{joined}\n"
    )


def validate_voice_profile(raw: dict[str, object]) -> VoiceProfile:
    """Validate a model-produced voice profile against the fixed contract."""

    try:
        profile = VoiceProfile.model_validate(raw)
    except ValidationError as error:
        raise ContractError(
            "voice_profile_invalid",
            detail=f"문체 프로필이 계약을 위반했습니다: {error.errors()[0].get('msg', '')}",
        ) from error
    return profile
