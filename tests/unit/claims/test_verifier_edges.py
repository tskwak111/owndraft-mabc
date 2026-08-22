"""Regression tests for strict verification edge cases found in final audit."""


from owndraft.claims.locker import extract_deterministic_claims
from owndraft.claims.verifier import verify_preservation
from owndraft.contracts.stage1 import Claim, EditMode, Stage1Request


def _request(text: str, locked: list[str] | None = None) -> Stage1Request:
    return Stage1Request(
        text=text,
        purpose="검증",
        audience="독자",
        edit_mode=EditMode.MINIMAL,
        locked_phrases=locked or [],
    )


def _claim(text_request: Stage1Request, value_substring: str) -> Claim:
    claims = extract_deterministic_claims(text_request)
    for claim in claims:
        if claim.normalized_value.replace(" ", "") == value_substring.replace(" ", ""):
            return claim
    raise AssertionError(f"클레임 미추출: {value_substring}")


def test_comma_separated_number_survives_without_separators():
    request = _request("연간 구독료는 총 1,200,000원이다.")
    claim = _claim(request, "1,200,000원")

    rewritten = "연간 구독료는 총 1200000원이다."
    report = verify_preservation([claim], rewritten)

    assert report.passed is True


def test_comma_number_rephrased_as_manwon_is_rejected():
    request = _request("연간 구독료는 총 1,200,000원이다.")
    claim = _claim(request, "1,200,000원")

    rewritten = "연간 구독료는 총 120만 원이다."
    report = verify_preservation([claim], rewritten)

    assert report.passed is False
    assert {issue.code for issue in report.issues} & {"locked_value_missing", "unit_changed"}


def test_unit_change_is_detected_for_same_number():
    request = _request("이번 주간 회의는 40분 동안 진행됐습니다.")
    claim = _claim(request, "40분")

    rewritten = "이번 주간 회의는 40시간 동안 진행됐습니다."
    report = verify_preservation([claim], rewritten)

    assert report.passed is False
    assert any(issue.code == "unit_changed" for issue in report.issues)


def test_relative_rephrasing_of_date_is_rejected():
    request = _request("이번 과제의 마감 기한은 8월 28일입니다.")
    claim = _claim(request, "8월 28일")

    report = verify_preservation([claim], "이번 과제의 마감 기한은 이달 마지막 주입니다.")
    assert report.passed is False

    report_ok = verify_preservation([claim], "이번 과제 마감은 8월 28일로 확정됐다.")
    assert report_ok.passed is True


def test_hour_words_do_not_become_clock_time_claims():
    request = _request("학습 시간은 6시간에서 9시간으로 늘었다.")

    time_claims = [c for c in extract_deterministic_claims(request) if c.claim_type == "time"]
    assert time_claims == []

    number_values = {
        c.normalized_value for c in extract_deterministic_claims(request) if c.claim_type == "number"
    }
    assert {"6시간", "9시간"} <= number_values


def test_clock_time_is_still_claimed():
    request = _request("오늘 예정된 전체 회의는 오후 3시에 시작합니다.")

    time_values = {
        c.normalized_value for c in extract_deterministic_claims(request) if c.claim_type == "time"
    }
    assert any("3시" in value for value in time_values)
