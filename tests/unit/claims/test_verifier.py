import pytest
from owndraft.claims.locker import extract_deterministic_claims
from owndraft.claims.verifier import verify_preservation
from owndraft.contracts.stage1 import EditMode, Stage1Request

ORIGINAL = (
    'Solar를 쓴 뒤 회의록 정리가 40분에서 5분으로 줄었다. '
    '자료는 https://example.com에 있고, 나는 "완전히 자동화된 것은 아니다"라고 썼다.'
)


@pytest.fixture
def sample_claims():
    request = Stage1Request(
        text=ORIGINAL,
        purpose="블로그",
        audience="대학생",
        edit_mode=EditMode.MINIMAL,
        locked_phrases=["Solar"],
    )
    return extract_deterministic_claims(request)


def test_verifier_accepts_faithful_rewrite(sample_claims):
    rewritten = (
        'Solar를 쓰고 나서 회의록 정리가 40분 걸리던 게 5분으로 줄었다. '
        '"완전히 자동화된 것은 아니다"라는 점도 그대로다. 자료는 https://example.com에 있다.'
    )
    report = verify_preservation(sample_claims, rewritten, model_claims=[])

    assert report.passed is True
    assert report.new_claim_count == 0


def test_verifier_rejects_changed_number_and_dropped_negation(sample_claims):
    rewritten = "Solar를 쓴 뒤 회의록 정리가 30분에서 5분으로 줄었고 완전히 자동화됐다."
    report = verify_preservation(sample_claims, rewritten, model_claims=[])

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {
        "locked_value_missing",
        "polarity_changed",
    }


def test_verifier_rejects_missing_url(sample_claims):
    rewritten = '회의록 정리가 40분에서 5분으로 줄었고 "완전히 자동화된 것은 아니다".'
    report = verify_preservation(sample_claims, rewritten, model_claims=[])

    assert report.passed is False
    assert any(issue.code == "source_changed" for issue in report.issues)


def test_verifier_counts_model_reported_new_claims(sample_claims):
    rewritten = (
        'Solar를 쓴 뒤 회의록 정리가 40분에서 5분으로 줄었다. '
        '자료는 https://example.com에 있고, "완전히 자동화된 것은 아니다". '
        '정확도가 95%에 달한다.'
    )
    from owndraft.contracts.stage1 import Claim

    model_new = Claim(
        id="m_0001",
        claim_type="number",
        source_text="정확도가 95%",
        normalized_value="정확도가 95%",
        start=0,
        end=7,
        locked=False,
        evidence_type="new_statistic",
    )
    report = verify_preservation(
        sample_claims,
        rewritten,
        model_claims=[model_new],
        unsupported_new_claims=[model_new],
    )

    assert report.passed is False
    assert report.new_claim_count >= 1


def test_verifier_tolerates_deleted_style_text(sample_claims):
    rewritten = "40분에서 5분으로 줄었다."
    report = verify_preservation(sample_claims, rewritten, model_claims=[])

    # numbers survive; URL/quote/negation loss still fails
    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {"source_changed"}
