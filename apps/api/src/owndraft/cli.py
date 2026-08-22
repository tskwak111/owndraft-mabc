"""OwnDraft command line interface.

`evaluate` executes the 20-case offline regression suite and writes JSON and
Markdown reports. Exit code is 0 only when every stage 1 quality gate passes.
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from owndraft.evaluation.fixtures import load_cases
from owndraft.evaluation.runner import OfflineEvaluationRunner, render_markdown_report

app = typer.Typer(help="OwnDraft stage 1 skill harness")


@app.callback()
def _root() -> None:
    """OwnDraft 명령줄 도구."""


GATE_TARGETS = {
    "total_cases": 20,
    "min_average_pattern_reduction": 0.60,
    "min_average_semantic_fidelity": 4.5,
    "max_severe_locked_fact_errors": 0,
    "max_unsupported_new_facts": 0,
}


def _evaluate(cases: Path, output: Path, markdown: Path) -> int:
    cases_loaded = load_cases(Path(cases))
    if len(cases_loaded) != GATE_TARGETS["total_cases"]:
        typer.echo(
            f"FAIL: 평가 케이스는 정확히 {GATE_TARGETS['total_cases']}개여야 합니다: {len(cases_loaded)}개"
        )
        return 1

    runner = OfflineEvaluationRunner()
    report = asyncio.run(runner.run(Path(cases)))
    report.metadata["generated_at"] = datetime.now(UTC).isoformat()

    summary = report.summary
    failures: list[str] = []
    if summary["completed_cases"] != GATE_TARGETS["total_cases"]:
        failures.append(f"완료 케이스 부족: {summary['completed_cases']}/20")
    if summary["severe_locked_fact_errors"] != GATE_TARGETS["max_severe_locked_fact_errors"]:
        failures.append(f"잠긴 사실 심각 오류: {summary['severe_locked_fact_errors']}")
    if summary["unsupported_new_facts"] != GATE_TARGETS["max_unsupported_new_facts"]:
        failures.append(f"지원되지 않는 새 사실: {summary['unsupported_new_facts']}")
    if float(summary["average_pattern_reduction"]) < GATE_TARGETS["min_average_pattern_reduction"]:
        failures.append(
            f"평균 패턴 감소율 미달: {float(summary['average_pattern_reduction']):.2f} < 0.60"
        )
    if float(summary["average_semantic_fidelity"]) < GATE_TARGETS["min_average_semantic_fidelity"]:
        failures.append(
            f"평균 의미 충실도 미달: {float(summary['average_semantic_fidelity']):.2f} < 4.5"
        )
    if summary["voice_mode_cases"] > 0 and float(summary["voice_mode_average_constraint_match"]) < 0.90:
        failures.append(
            f"voice 제약 일치율 미달: {float(summary['voice_mode_average_constraint_match']):.2f} < 0.90"
        )
    if any(case.repair_attempts > 1 for case in report.cases):
        failures.append("repair 1회 초과 케이스 존재")

    output.parent.mkdir(parents=True, exist_ok=True)
    markdown.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    markdown.write_text(render_markdown_report(report), encoding="utf-8")

    typer.echo(f"보고서 저장: {output}")
    typer.echo(f"보고서 저장: {markdown}")
    if failures:
        for failure in failures:
            typer.echo(f"FAIL: {failure}")
        return 1
    typer.echo("OK: 모든 품질 게이트 통과")
    return 0


@app.command()
def evaluate(
    cases: Annotated[Path, typer.Option(..., "--cases", help="평가 케이스 YAML 디렉터리")],
    output: Annotated[Path, typer.Option(..., "--output", help="JSON 보고서 경로")],
    markdown: Annotated[Path, typer.Option(..., "--markdown", help="Markdown 보고서 경로")],
) -> None:
    """Run the stage 1 evaluation suite (deterministic fake gateway)."""

    raise typer.Exit(_evaluate(cases=cases, output=output, markdown=markdown))


if __name__ == "__main__":
    app()
