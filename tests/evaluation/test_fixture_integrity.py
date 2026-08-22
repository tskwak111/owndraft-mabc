from pathlib import Path

import pytest
from owndraft.contracts.stage1 import Stage1Request
from owndraft.evaluation.fixtures import load_cases
from owndraft.patterns.catalog import load_pattern_catalog
from owndraft.patterns.scanner import scan_deterministic_patterns
from owndraft.text.segmentation import segment_text

CASES_DIR = Path("packages/evaluation/cases")


def test_all_twenty_cases_have_required_labels():
    cases = load_cases(CASES_DIR)

    assert len(cases) == 20
    assert len({case.id for case in cases}) == 20
    for case in cases:
        assert case.locked_values
        assert case.expected_pattern_codes
        assert case.forbidden_new_claims
        assert case.allowed_edit_summary


def test_case_categories_have_five_each():
    cases = load_cases(CASES_DIR)
    by_category = {category: [] for category in ("blog", "email", "report", "social")}

    for case in cases:
        by_category[case.category].append(case.id)

    for category, ids in by_category.items():
        assert len(ids) == 5, f"{category}: {ids}"


def test_fixture_texts_are_realistic_length():
    for case in load_cases(CASES_DIR):
        assert 120 <= len(case.request.text) <= 900, case.id


def test_expected_pattern_codes_are_catalog_codes_and_detectable():
    catalog = load_pattern_catalog()
    known_codes = {rule.code for rule in catalog}

    for case in load_cases(CASES_DIR):
        unknown = set(case.expected_pattern_codes) - known_codes
        assert not unknown, f"{case.id}: {unknown}"

        request = Stage1Request(
            text=case.request.text,
            purpose=case.request.purpose,
            audience=case.request.audience,
            edit_mode=case.request.edit_mode,
            voice_samples=case.request.voice_samples,
            locked_phrases=case.request.locked_phrases,
        )
        spans = segment_text(request.text)
        detected = {
            finding.pattern_code
            for finding in scan_deterministic_patterns(spans, catalog)
        }
        missing = set(case.expected_pattern_codes) - detected
        assert not missing, (
            f"{case.id}: 레이블 코드 중 결정론적 스캔에 잡히지 않는 것: {missing}"
        )


def test_locked_values_exist_in_text_or_context_answers():
    for case in load_cases(CASES_DIR):
        haystack = case.request.text + "\n" + "\n".join(case.context_answers.values())
        for value in case.locked_values:
            normalized = value.replace(" ", "")
            assert normalized in haystack.replace(" ", ""), (
                f"{case.id}: 잠금 값 '{value}'가 원문/답변에 없음"
            )


@pytest.mark.parametrize(
    "case_id",
    [
        "blog_01_meeting_minutes",
        "email_01_schedule_change",
        "report_01_experiment_result",
        "social_01_product_launch",
    ],
)
def test_representative_case_ids_exist(case_id: str):
    ids = {case.id for case in load_cases(CASES_DIR)}

    assert case_id in ids
