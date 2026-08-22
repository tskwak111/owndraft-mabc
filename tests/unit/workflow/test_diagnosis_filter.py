import pytest

from tests.unit.workflow.conftest import REQUEST_WITH_ABSTRACT_CLAIM

pytestmark = pytest.mark.asyncio


async def test_model_findings_with_hallucinated_spans_are_dropped(workflow, fake_gateway):
    fake_gateway.set_response(
        "scan_patterns",
        {
            "findings": [
                {
                    "span_id": "s_9999",
                    "pattern_code": "fake_depth_phrase",
                    "severity": "low",
                    "reason": "환각 스팬",
                    "action": "rewrite",
                },
                {
                    "span_id": "s_0001",
                    "pattern_code": "era_background_intro",
                    "severity": "medium",
                    "reason": "시대 배경 서론",
                    "action": "delete",
                },
            ]
        },
    )

    result = await workflow.run(REQUEST_WITH_ABSTRACT_CLAIM)

    codes = {finding.pattern_code for finding in result.diagnosis}
    assert "fake_depth_phrase" not in codes
    assert "era_background_intro" in codes
    assert all(finding.span_id.startswith("s_") for finding in result.diagnosis)
