import pytest
from owndraft.contracts.stage1 import EditMode, Stage1Request
from pydantic import ValidationError


def test_stage1_request_rejects_oversized_text():
    with pytest.raises(ValidationError):
        Stage1Request(
            text="가" * 10_001,
            purpose="블로그 글",
            audience="대학생",
            edit_mode=EditMode.VOICE,
        )


def test_stage1_request_rejects_too_short_text():
    with pytest.raises(ValidationError):
        Stage1Request(text="짧은 원문", purpose="블로그", audience="독자")


def test_voice_mode_requires_at_least_80_sample_characters():
    request = Stage1Request(
        text="회의록 작성 경험을 설명하는 충분히 긴 원문입니다." * 2,
        purpose="블로그 글",
        audience="대학생",
        edit_mode=EditMode.VOICE,
        voice_samples=["짧은 샘플"],
    )
    assert request.effective_edit_mode is EditMode.MINIMAL
    assert request.voice_sample_confidence == "none"


def test_voice_sample_confidence_boundaries():
    def make_request(samples: list[str]) -> Stage1Request:
        return Stage1Request(
            text="회의록 작성 경험을 설명하는 충분히 긴 원문입니다." * 4,
            purpose="블로그",
            audience="대학생",
            edit_mode=EditMode.VOICE,
            voice_samples=samples,
        )

    assert make_request(["나" * 79]).voice_sample_confidence == "none"
    assert make_request(["나" * 80]).voice_sample_confidence == "low"
    assert make_request(["나" * 159]).voice_sample_confidence == "low"
    assert make_request(["나" * 160]).voice_sample_confidence == "medium"
    assert make_request(["나" * 399]).voice_sample_confidence == "medium"
    assert make_request(["나" * 400, "나" * 10]).voice_sample_confidence == "high"


def test_voice_mode_with_sufficient_samples_stays_voice():
    sample = "나는 결론부터 말하고 이유를 붙이는 편이다. 근거 없는 수식어는 쓰지 않는다." * 2
    request = Stage1Request(
        text="회의록 작성 경험을 설명하는 충분히 긴 원문입니다." * 4,
        purpose="블로그",
        audience="대학생",
        edit_mode=EditMode.VOICE,
        voice_samples=[sample],
    )
    assert request.voice_sample_chars >= 80
    assert request.effective_edit_mode is EditMode.VOICE


def test_stage1_request_rejects_more_than_three_voice_samples():
    with pytest.raises(ValidationError):
        Stage1Request(
            text="회의록 작성 경험을 설명하는 충분히 긴 원문입니다." * 4,
            purpose="블로그",
            audience="대학생",
            voice_samples=["샘플"] * 4,
        )
