"""Deterministic Korean rendering of Stage1Result for the end user.

The renderer emits exactly the headings defined in skills/owndraft/SKILL.md and
never exposes internal scores or trace metadata.
"""

from owndraft.contracts.stage1 import PreservationReport, Stage1Request, Stage1Result

_DIAGNOSIS_HEADING = "## 진단 요약"
_QUESTIONS_HEADING = "## 확인할 내용"
_LOCKED_HEADING = "## 현재 보존 중인 사실"
_REWRITE_HEADING = "## 수정본"
_CHANGES_HEADING = "## 주요 변경 이유"
_PRESERVATION_HEADING = "## 사실 보존 결과"


def _diagnosis_lines(result: Stage1Result) -> list[str]:
    if result.diagnosis:
        return [f"- {finding.reason} ({finding.pattern_code})" for finding in result.diagnosis]
    return ["- 두드러진 상투 패턴은 발견되지 않았습니다."]


def _locked_lines(request: Stage1Request) -> list[str]:
    lines: list[str] = []
    for phrase in request.locked_phrases:
        lines.append(f"- 잠금 표현: {phrase}")
    return lines or ["- 사용자가 지정한 잠금 표현 없음"]


def _preservation_lines(report: PreservationReport) -> list[str]:
    status = "통과" if report.passed else "미통과"
    lines = [
        f"- 검증 결과: {status} (잠긴 항목 {report.preserved_locked}/{report.locked_total}, 새 사실 {report.new_claim_count}개)"
    ]
    for issue in report.issues:
        marker = issue.code
        if issue.detail:
            lines.append(f"- 문제({marker}): {issue.detail}")
        else:
            lines.append(f"- 문제({marker})")
    return lines


def render_stage1_result(result: Stage1Result, request: Stage1Request) -> str:
    """Render a user-facing Korean answer for one workflow outcome."""

    sections: list[str] = [_DIAGNOSIS_HEADING, *_diagnosis_lines(result)]

    if result.status == "needs_context":
        sections.append(_QUESTIONS_HEADING)
        for index, question in enumerate(result.questions, start=1):
            sections.append(f"{index}. {question.question}")
        sections.append(_LOCKED_HEADING)
        sections.extend(_locked_lines(request))
        return "\n".join(sections).strip() + "\n"

    if result.status == "completed" and result.rewritten_text is not None:
        sections.extend([_REWRITE_HEADING, result.rewritten_text.strip()])
        sections.append(_CHANGES_HEADING)
        if result.changes:
            sections.extend(f"- {change.reason}" for change in result.changes)
        else:
            sections.append("- 의미 있는 구조 변경 없음")
        sections.append(_PRESERVATION_HEADING)
        if result.preservation is not None:
            sections.extend(_preservation_lines(result.preservation))
        else:
            sections.append("- 검증 결과 정보 없음")
        return "\n".join(sections).strip() + "\n"

    # blocked
    sections.append(_LOCKED_HEADING)
    sections.extend(_locked_lines(request))
    sections.append("## 실패 사유")
    if result.preservation is not None:
        sections.extend(_preservation_lines(result.preservation))
    sections.append("- 권고: 원문을 유지하고 아래 항목을 직접 확인해 주세요.")
    return "\n".join(sections).strip() + "\n"
