"""Offline evaluation runner: executes the full workflow per case deterministically.

The offline candidate is produced by a deterministic rule (remove detected
pattern phrases, keep every locked anchor verbatim, weave in user answers), so
the whole 20-case suite runs in CI with no API key. Live-model comparison
baselines are an explicit manual step and are never faked here.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from owndraft.claims.locker import extract_deterministic_claims
from owndraft.claims.verifier import verify_preservation
from owndraft.contracts.stage1 import (
    ChangeReason,
    Claim,
    EditMode,
    PatternFinding,
    Stage1Request,
)
from owndraft.evaluation.fixtures import EvaluationCase, load_cases
from owndraft.evaluation.metrics import EvaluationResult, aggregate_results
from owndraft.llm.gateway import FakeModelGateway
from owndraft.text.normalization import normalize_for_comparison
from owndraft.text.segmentation import segment_text

_PASSED_FACT = {
    "critic": "fact",
    "score": 5.0,
    "passed": True,
    "new_claim_count": 0,
    "severe_error_count": 0,
}
_PASSED_FIDELITY = {"critic": "fidelity", "score": 5.0, "passed": True}
_PASSED_NATURALNESS = {"critic": "naturalness", "score": 5.0, "passed": True}


def build_offline_candidate(
    request: Stage1Request,
    answers: dict[str, str],
    findings: list[PatternFinding],
) -> str:
    """Deterministic candidate: strip matched pattern phrases, keep the rest.

    Locked anchors outside the matched phrases survive untouched because only
    exact rule regexes are substituted.
    """

    from owndraft.patterns.catalog import load_pattern_catalog

    catalog = load_pattern_catalog()
    kept_parts: list[str] = []
    for span in segment_text(request.text):
        text = span.text
        for rule in catalog:
            for pattern in rule.regexes:
                text = re.sub(pattern, "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        text = text.lstrip(",-· ").strip()
        if len(text) >= 2:
            if not text.endswith((".", "!", "?")):
                text += "."
            kept_parts.append(text)

    answer_text = " ".join(answer.strip() for answer in answers.values() if answer.strip())
    if answer_text:
        if not answer_text.endswith((".", "!", "?")):
            answer_text += "."
        kept_parts.append(answer_text)
    return "\n".join(part for part in kept_parts if part)


def _combined_request(request: Stage1Request, answers: dict[str, str]) -> Stage1Request:
    joined_answers = "\n".join(answers.values())
    combined_text = request.text + ("\n" + joined_answers if joined_answers else "")
    return Stage1Request(
        text=combined_text[:10_000],
        purpose=request.purpose,
        audience=request.audience,
        edit_mode=EditMode.MINIMAL,
        voice_samples=[],
        locked_phrases=request.locked_phrases,
    )


def _required_meaning_score(candidate: str, required_meaning: list[str]) -> float:
    haystack = normalize_for_comparison(candidate).replace(" ", "")
    matched = sum(
        1
        for phrase in required_meaning
        if all(token in haystack for token in normalize_for_comparison(phrase).replace(" ", "").split())
    )
    total = max(1, len(required_meaning))
    fraction = matched / total
    if fraction >= 0.6:
        return 5.0
    if fraction > 0:
        return 3.0
    return 1.0


@dataclass
class CaseReport:
    case_id: str
    category: str
    status: str
    passed: bool
    repair_attempts: int
    metrics: EvaluationResult
    issues: list[str] = field(default_factory=list)


@dataclass
class EvaluationRunReport:
    cases: list[CaseReport]
    summary: dict[str, float | int]
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "metadata": self.metadata,
            "cases": [
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "status": case.status,
                    "passed": case.passed,
                    "repair_attempts": case.repair_attempts,
                    "metrics": case.metrics.model_dump(),
                    "issues": case.issues,
                }
                for case in self.cases
            ],
        }


def render_markdown_report(report: EvaluationRunReport) -> str:
    lines = [
        "# OwnDraft STAGE 1 평가 보고서",
        "",
        f"- 모델: {report.metadata.get('model', 'fake-gateway')}",
        f"- 스킬 버전: {report.metadata.get('skill_version', 'unknown')}",
        f"- 생성 시각: {report.metadata.get('generated_at', 'unknown')}",
        "",
        "## 요약",
        "",
        f"- 케이스: {report.summary['total_cases']}개",
        f"- 완료: {report.summary['completed_cases']}개",
        f"- 잠긴 사실 심각 오류: {report.summary['severe_locked_fact_errors']}개",
        f"- 지원되지 않는 새 사실: {report.summary['unsupported_new_facts']}개",
        f"- 평균 패턴 감소율: {float(report.summary['average_pattern_reduction']):.2f}",
        f"- 평균 의미 충실도: {float(report.summary['average_semantic_fidelity']):.2f}/5",
        f"- voice 모드 제약 일치율: {float(report.summary['voice_mode_average_constraint_match']):.2f} ({report.summary['voice_mode_cases']}개)",
        "",
        "## 케이스 결과",
        "",
        "| case_id | category | status | passed | repair | preservation | pattern_reduction | fidelity | voice |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for case in report.cases:
        m = case.metrics
        voice = "-" if m.voice_constraint_match is None else f"{m.voice_constraint_match:.0%}"
        preserved = "100%" if m.locked_fact_preservation >= 1 else f"{m.locked_fact_preservation:.0%}"
        lines.append(
            f"| {case.case_id} | {case.category} | {case.status} | "
            f"{'PASS' if case.passed else 'FAIL'} | {case.repair_attempts} | "
            f"{preserved} | {m.pattern_reduction:.0%} | {m.semantic_fidelity:.1f} | {voice} |"
        )
    return "\n".join(lines) + "\n"


class OfflineEvaluationRunner:
    """Runs all cases through Stage1Workflow with deterministic fixtures."""

    def __init__(self) -> None:
        self._workflow_cache: FakeModelGateway | None = None

    async def run_case(self, case: EvaluationCase) -> CaseReport:
        request = case.to_stage1_request()

        spans = segment_text(request.text)
        from owndraft.patterns.catalog import load_pattern_catalog
        from owndraft.patterns.scanner import scan_deterministic_patterns

        catalog = load_pattern_catalog()
        before_findings = scan_deterministic_patterns(spans, catalog)

        candidate_text = build_offline_candidate(request, case.context_answers, before_findings)
        candidate_changes = [
            ChangeReason(span_id=f.span_id, change_type="rewrite", reason=f.reason).model_dump()
            for f in before_findings
        ]
        candidate_payload = {
            "rewritten_text": candidate_text,
            "change_reasons": candidate_changes,
        }

        gateway = FakeModelGateway({})
        gateway.set_response("extract_claims", {"claims": []})
        gateway.set_response("scan_patterns", {"findings": []})
        gateway.set_response("find_context_gaps", {"questions": []})
        gateway.set_response("plan_rewrite", {"goals": [case.labels.allowed_edit_summary], "operations": []})
        gateway.set_response("write_candidate", candidate_payload)
        gateway.set_response("repair_candidate", dict(candidate_payload))
        gateway.set_response("profile_voice", {
            "language": "ko",
            "sample_chars": sum(len(s.strip()) for s in request.voice_samples),
            "confidence": request.voice_sample_confidence,
        })
        gateway.set_response("critic_fact", _PASSED_FACT)
        gateway.set_response("critic_fidelity", _PASSED_FIDELITY)
        gateway.set_response(
            "critic_voice",
            {"critic": "voice", "score": 5.0, "passed": True, "constraint_match": 1.0},
        )
        gateway.set_response("critic_naturalness", _PASSED_NATURALNESS)

        from owndraft.workflow.stage1 import Stage1Workflow

        workflow = Stage1Workflow(gateway)
        result = await workflow.run(request, context_answers=case.context_answers)

        # deterministic verification against source + user answers
        claims: list[Claim] = extract_deterministic_claims(
            _combined_request(request, case.context_answers)
        )
        preservation = verify_preservation(claims, result.rewritten_text or "")
        after_spans = segment_text(result.rewritten_text or "")
        after_findings = scan_deterministic_patterns(after_spans, catalog)

        forbidden_found = sum(
            1
            for phrase in case.labels.forbidden_new_claims
            if normalize_for_comparison(phrase) in normalize_for_comparison(candidate_text)
        )
        output_claims = len([claim for claim in claims if claim.claim_type == "number"])
        new_claim_rate = forbidden_found / max(1, output_claims)

        before_count = len(before_findings)
        after_count = len(after_findings)
        pattern_reduction = max(0.0, min(1.0, (before_count - after_count) / max(1, before_count)))

        voice_match: float | None = None
        if request.edit_mode is EditMode.VOICE and request.voice_sample_confidence != "none":
            checks = [
                not any(f.pattern_code == "chatbot_greeting_closing" for f in after_findings),
                not any(f.pattern_code == "promotional_superlative" for f in after_findings),
                bool(candidate_text.strip()),
            ]
            voice_match = sum(checks) / len(checks)

        fidelity = _required_meaning_score(candidate_text, case.labels.required_meaning)

        metrics = EvaluationResult(
            locked_fact_preservation=(
                preservation.preserved_locked / preservation.locked_total
                if preservation.locked_total
                else 1.0
            ),
            new_claim_rate=new_claim_rate,
            semantic_fidelity=fidelity,
            pattern_reduction=pattern_reduction,
            voice_constraint_match=voice_match,
            severe_locked_fact_errors=preservation.high_severity_issue_count,
        )

        issues = [f"{issue.code}: {issue.detail}" for issue in preservation.issues]
        return CaseReport(
            case_id=case.id,
            category=case.category,
            status=result.status,
            passed=result.status == "completed" and metrics.passed,
            repair_attempts=result.preservation.repair_attempts if result.preservation else 0,
            metrics=metrics,
            issues=issues,
        )

    async def run(self, cases_dir: Path) -> EvaluationRunReport:
        cases = load_cases(Path(cases_dir))
        reports = [await self.run_case(case) for case in cases]
        results = [case.metrics for case in reports]
        aggregate = aggregate_results(results)
        severe_errors = sum(r.severe_locked_fact_errors for r in results)
        new_facts = sum(1 for r in results if r.new_claim_rate > 0)
        summary: dict[str, float | int] = {
            **aggregate,
            "completed_cases": sum(1 for r in reports if r.status == "completed"),
            "severe_locked_fact_errors": severe_errors,
            "unsupported_new_facts": new_facts,
            "failed_cases": sum(1 for r in reports if not r.passed),
        }

        from scripts.export_timely_skill import build_export_text

        from owndraft.patterns.catalog import find_repo_root

        try:
            _, digest = build_export_text(find_repo_root())
            skill_version = digest[:12]
        except (OSError, FileNotFoundError):
            skill_version = "unavailable"

        return EvaluationRunReport(
            cases=reports,
            summary=summary,
            metadata={
                "model": "fake-gateway(deterministic)",
                "skill_version": skill_version,
                "cases_dir": str(cases_dir),
            },
        )
