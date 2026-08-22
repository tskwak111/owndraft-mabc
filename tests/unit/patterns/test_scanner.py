from owndraft.patterns.catalog import load_pattern_catalog
from owndraft.patterns.scanner import scan_deterministic_patterns
from owndraft.text.segmentation import segment_text


def test_scanner_finds_high_precision_korean_patterns():
    text = (
        "빠르게 변화하는 현대 사회에서 AI는 단순한 도구를 넘어 핵심 파트너입니다. "
        "결론적으로 앞으로 더욱 중요해질 것으로 기대됩니다."
    )
    findings = scan_deterministic_patterns(segment_text(text), load_pattern_catalog())
    codes = {finding.pattern_code for finding in findings}

    assert "era_background_intro" in codes
    assert "beyond_x_to_y" in codes
    assert "automatic_conclusion_marker" in codes
    assert "unsupported_future_outlook" in codes


def test_scanner_findings_reference_valid_spans():
    text = "빠르게 변화하는 디지털 시대에서 업무 방식이 달라지고 있습니다. 안녕하세요! 감사합니다."
    spans = segment_text(text)
    span_ids = {span.id for span in spans}
    findings = scan_deterministic_patterns(spans, load_pattern_catalog())

    assert findings
    assert all(finding.span_id in span_ids for finding in findings)


def test_scanner_deduplicates_by_span_and_code():
    text = "빠르게 변화하는 현대 사회에서 모든 것이 바뀝니다."
    spans = segment_text(text)
    findings = scan_deterministic_patterns(spans, load_pattern_catalog())

    keys = [(finding.span_id, finding.pattern_code) for finding in findings]
    assert len(keys) == len(set(keys))


def test_scanner_returns_empty_for_clean_text():
    text = "어제 오후 세 시에 회의를 했다. 다음 주 화요일까지 결과를 정리해서 보내겠다."
    findings = scan_deterministic_patterns(segment_text(text), load_pattern_catalog())

    assert findings == []
