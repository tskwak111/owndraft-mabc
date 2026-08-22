from owndraft.claims.locker import extract_deterministic_claims
from owndraft.contracts.stage1 import EditMode, Stage1Request


def test_claim_locker_extracts_numbers_product_url_quote_and_negation():
    request = Stage1Request(
        text=(
            'Solar를 쓴 뒤 회의록 정리가 40분에서 5분으로 줄었다. '
            '자료는 https://example.com에 있고, 나는 "완전히 자동화된 것은 아니다"라고 썼다.'
        ),
        purpose="블로그",
        audience="대학생",
        edit_mode=EditMode.MINIMAL,
        locked_phrases=["Solar"],
    )
    claims = extract_deterministic_claims(request)
    values = {claim.normalized_value for claim in claims}

    assert "Solar" in values
    assert "40분" in values
    assert "5분" in values
    assert "https://example.com" in values
    assert "완전히 자동화된 것은 아니다" in values
    assert any(claim.claim_type == "negation" for claim in claims)


def test_claim_locker_offsets_point_at_original_text():
    request = Stage1Request(
        text="2026년 8월 31일까지 예산 500만 원을 승인받아야 한다.",
        purpose="메일",
        audience="팀장",
        edit_mode=EditMode.MINIMAL,
    )
    claims = extract_deterministic_claims(request)
    original = request.text

    for claim in claims:
        assert claim.start < claim.end <= len(original)
        assert original[claim.start : claim.end] == claim.source_text


def test_claim_locker_extracts_dates_units_emails_and_conditionals():
    request = Stage1Request(
        text=(
            "매주 월요일 오전 9시에 보고하며, 금액은 1,200,000원이다. "
            "문의는 team@example.com으로. 단, 서버 장애 시에는 제외한다."
        ),
        purpose="보고서",
        audience="리더",
        edit_mode=EditMode.MINIMAL,
    )
    types = {claim.claim_type for claim in extract_deterministic_claims(request)}

    assert {"date", "number", "email", "conditional"} <= types


def test_claim_locker_deduplicates_exact_duplicates():
    request = Stage1Request(
        text="비용은 5만원이고 추가 비용도 5만원이다.",
        purpose="메모",
        audience="동료",
        edit_mode=EditMode.MINIMAL,
    )
    claims = extract_deterministic_claims(request)
    keys = [(claim.start, claim.end, claim.claim_type) for claim in claims]

    assert len(keys) == len(set(keys))


def test_locked_phrase_overlaps_are_kept():
    request = Stage1Request(
        text="Upstage Solar Pro 모델로 문서를 요약했다.",
        purpose="블로그",
        audience="독자",
        edit_mode=EditMode.MINIMAL,
        locked_phrases=["Solar Pro"],
    )
    claims = extract_deterministic_claims(request)

    solar_claims = [c for c in claims if c.normalized_value == "Solar Pro"]
    assert len(solar_claims) == 1
