
from owndraft.contracts.stage1 import (
    ChangeReason,
    ContextQuestion,
    EditMode,
    PreservationIssue,
    PreservationReport,
    Stage1Request,
    Stage1Result,
)
from owndraft.prompts.renderer import render_stage1_result

REQUEST = Stage1Request(
    text="회의록 작성 경험을 설명하는 충분히 긴 원문입니다. 여기에는 사실이 담겨 있습니다.",
    purpose="블로그",
    audience="대학생",
    edit_mode=EditMode.MINIMAL,
)


def _result(**overrides) -> Stage1Result:
    base = {
        "status": "completed",
        "trace_id": "trace-123",
        "diagnosis": [],
        "questions": [],
        "rewritten_text": None,
        "changes": [],
        "preservation": None,
    }
    base.update(overrides)
    return Stage1Result.model_construct(**base)


def test_needs_context_rendering_uses_exact_skill_headings():
    result = _result(
        status="needs_context",
        questions=[
            ContextQuestion(
                id="q1",
                question="실제로 줄어든 시간이 얼마인가요?",
                target_gap="metric",
                expected_answer_type="number",
            )
        ],
    )

    rendered = render_stage1_result(result, REQUEST)

    assert "## 진단 요약" in rendered
    assert "## 확인할 내용" in rendered
    assert "## 현재 보존 중인 사실" in rendered
    assert "1. 실제로 줄어든 시간이 얼마인가요?" in rendered
    assert "## 수정본" not in rendered
    assert "trace-123" not in rendered


def test_completed_rendering_includes_preservation_status():
    result = _result(
        status="completed",
        rewritten_text="수정된 본문",
        changes=[ChangeReason(span_id="s_0001", change_type="delete", reason="서론 삭제")],
        preservation=PreservationReport(passed=True, locked_total=2, preserved_locked=2),
    )

    rendered = render_stage1_result(result, REQUEST)

    assert "## 수정본" in rendered
    assert "수정된 본문" in rendered
    assert "## 주요 변경 이유" in rendered
    assert "- 서론 삭제" in rendered
    assert "## 사실 보존 결과" in rendered
    assert "잠긴 항목 2/2" in rendered
    assert "새 사실 0개" in rendered


def test_blocked_rendering_reports_problem_and_keeps_original_recommendation():
    result = _result(
        status="blocked",
        preservation=PreservationReport(
            passed=False,
            locked_total=2,
            preserved_locked=1,
            issues=[
                PreservationIssue(code="locked_value_missing", severity="high"),
            ],
        ),
    )

    rendered = render_stage1_result(result, REQUEST)

    assert "## 실패 사유" in rendered
    assert "locked_value_missing" in rendered
    assert "원문을 유지하고" in rendered
    assert "## 수정본" not in rendered


def test_renderer_never_exposes_trace_or_scores():
    result = _result(
        status="completed",
        rewritten_text="본문",
        preservation=PreservationReport(passed=True),
    )

    rendered = render_stage1_result(result, REQUEST)

    assert "trace" not in rendered.lower()
    assert "score" not in rendered.lower()
