import pytest
from owndraft.core.errors import ContractError
from owndraft.voice.profiler import (
    build_voice_profile_prompt,
    fallback_voice_profile,
    validate_voice_profile,
)


def test_fallback_profile_reports_low_confidence_for_short_sample():
    profile = fallback_voice_profile(["나는 결론부터 말하는 편이다." * 6])

    assert profile.confidence == "low"
    assert profile.sample_chars >= 80
    assert profile.sample_chars < 160


def test_fallback_profile_marks_heuristic_source_and_basic_fields():
    samples = [
        "결론부터 말한다. 근거는 두 개면 충분하다. 장식은 붙이지 않는다.",
        "짧게 끝낸다. 필요하면 예를 하나만 든다.",
    ]
    profile = fallback_voice_profile(samples)

    assert profile.source == "heuristic"
    assert profile.language == "ko"
    assert profile.sentence.average_length in {"short", "medium", "long"}
    assert profile.sentence.variance in {"low", "medium", "high"}
    assert 1 <= profile.paragraph.average_sentences <= 20
    assert profile.formality.level in {"casual", "polite", "formal"}


def test_fallback_profile_none_confidence_under_80_characters():
    profile = fallback_voice_profile(["아주 짧은 샘플 하나."])

    assert profile.confidence == "none"
    assert profile.sample_chars < 80


VALID_PROFILE_RAW = {
    "language": "ko",
    "formality": {"level": "polite", "honorific": True},
    "sentence": {"average_length": "short", "variance": "high"},
    "paragraph": {"average_sentences": 3, "spacing": "frequent"},
    "reasoning": {"order": ["conclusion", "reason"], "uncertainty_style": ["~인 것 같다"]},
    "punctuation": {"comma_frequency": "low", "parentheses_frequency": "medium"},
    "lexicon": {"preferred": ["일단"], "avoided": ["결론적으로"]},
    "rhetoric": {"list_preference": "flexible", "metaphor_frequency": "low"},
    "confidence": "medium",
    "sample_chars": 200,
}


def test_validate_voice_profile_accepts_wellformed_payload():
    profile = validate_voice_profile(VALID_PROFILE_RAW)

    assert profile.language == "ko"
    assert profile.lexicon.preferred == ["일단"]


def test_validate_voice_profile_rejects_verbatim_phrase_over_30_chars():
    raw = dict(VALID_PROFILE_RAW)
    raw["lexicon"] = {"preferred": ["아주 긴 문장을 그대로 베껴 오는 금지된 표현입니다열두글자더"], "avoided": []}

    with pytest.raises(ContractError):
        validate_voice_profile(raw)


def test_validate_voice_profile_rejects_more_than_ten_lexicon_items():
    raw = dict(VALID_PROFILE_RAW)
    raw["lexicon"] = {
        "preferred": [f"단어{i}" for i in range(11)],
        "avoided": [],
    }

    with pytest.raises(ContractError):
        validate_voice_profile(raw)


def test_build_voice_profile_prompt_contains_overcopy_guard():
    prompt = build_voice_profile_prompt(["나는 결론부터 말한다."], purpose="블로그")

    assert "샘플" in prompt
    assert ("복제하지" in prompt) or ("반복하지" in prompt)
    assert "블로그" in prompt
