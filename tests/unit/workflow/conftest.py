import pytest
from owndraft.contracts.stage1 import (
    EditMode,
    Stage1Request,
)
from owndraft.llm.gateway import FakeModelGateway
from owndraft.workflow.stage1 import Stage1Workflow

pytestmark = pytest.mark.asyncio

QUESTION_FIXTURE = {
    "id": "q_metric",
    "question": "회의록 정리에 실제로 걸리던 시간이 얼마였나요?",
    "target_gap": "metric",
    "expected_answer_type": "number",
}

REQUEST_WITH_ABSTRACT_CLAIM = Stage1Request(
    text=(
        "빠르게 변화하는 디지털 시대에 AI는 단순한 도구를 넘어 업무 혁신의 핵심 "
        "파트너가 되었습니다. 이를 통해 더 효율적이고 생산적인 결과를 만들 수 있습니다."
    ),
    purpose="AI 활용 경험 블로그",
    audience="대학생",
    edit_mode=EditMode.MINIMAL,
)

VALID_REQUEST = Stage1Request(
    text=(
        'Solar를 쓴 뒤 회의록 정리가 40분에서 5분으로 줄었다. '
        '자료는 https://example.com에 있고, 나는 "완전히 자동화된 것은 아니다"라고 썼다.'
    ),
    purpose="블로그",
    audience="대학생",
    edit_mode=EditMode.MINIMAL,
    locked_phrases=["Solar"],
)

FAITHFUL_CANDIDATE = {
    "rewritten_text": (
        'Solar를 쓰고 나서 회의록 정리가 40분 걸리던 일이 5분으로 줄었다. '
        '"완전히 자동화된 것은 아니다"라는 점도 그대로다. 자료는 https://example.com에 있다.'
    ),
    "change_reasons": [],
}

CANDIDATE_WITH_WRONG_30_MINUTES = {
    "rewritten_text": (
        "Solar를 쓴 뒤 회의록 정리가 30분에서 5분으로 줄었고 완전히 자동화됐다."
    ),
    "change_reasons": [],
}

CORRECTED_40_TO_5_MINUTES = FAITHFUL_CANDIDATE

FAILED_FACT_CRITIC = {
    "critic": "fact",
    "score": 2.0,
    "passed": False,
    "new_claim_count": 0,
    "severe_error_count": 1,
    "issues": ["locked_value_missing:40분"],
}

PASSED_FACT_CRITIC = {
    "critic": "fact",
    "score": 5.0,
    "passed": True,
    "new_claim_count": 0,
    "severe_error_count": 0,
}

DEFAULT_FIXTURES = {
    "extract_claims": {"claims": []},
    "scan_patterns": {"findings": []},
    "find_context_gaps": {"questions": []},
    "plan_rewrite": {"goals": [], "operations": []},
    "write_candidate": FAITHFUL_CANDIDATE,
    "critic_fact": PASSED_FACT_CRITIC,
    "critic_fidelity": {"critic": "fidelity", "score": 5.0, "passed": True},
    "critic_naturalness": {"critic": "naturalness", "score": 5.0, "passed": True},
}


@pytest.fixture
def fake_gateway():
    return FakeModelGateway(DEFAULT_FIXTURES)


@pytest.fixture
def workflow(fake_gateway):
    return Stage1Workflow(fake_gateway)
