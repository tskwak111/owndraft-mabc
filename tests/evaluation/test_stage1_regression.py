import json
from pathlib import Path

import pytest
from owndraft.evaluation.runner import OfflineEvaluationRunner

pytestmark = pytest.mark.asyncio

CASES_DIR = Path("packages/evaluation/cases")


async def test_offline_runner_completes_all_twenty_cases():
    runner = OfflineEvaluationRunner()

    report = await runner.run(CASES_DIR)

    assert report.summary["total_cases"] == 20
    assert report.summary["completed_cases"] == 20


async def test_offline_runner_meets_stage1_quality_gates(tmp_path: Path):
    runner = OfflineEvaluationRunner()
    report = await runner.run(CASES_DIR)
    summary = report.summary

    assert summary["severe_locked_fact_errors"] == 0
    assert summary["unsupported_new_facts"] == 0
    assert summary["average_pattern_reduction"] >= 0.60
    assert summary["average_semantic_fidelity"] >= 4.5
    if summary["voice_mode_cases"] > 0:
        assert summary["voice_mode_average_constraint_match"] >= 0.90
    assert all(case.repair_attempts <= 1 for case in report.cases)


async def test_report_serializes_to_json_and_markdown(tmp_path: Path):
    from owndraft.evaluation.runner import render_markdown_report

    runner = OfflineEvaluationRunner()
    report = await runner.run(CASES_DIR)

    json_path = tmp_path / "evaluation.json"
    md_path = tmp_path / "evaluation.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_report(report), encoding="utf-8")

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["summary"]["total_cases"] == 20
    assert "| case_id |" in md_path.read_text(encoding="utf-8")
