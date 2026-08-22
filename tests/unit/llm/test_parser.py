import pytest
from owndraft.contracts.stage1 import ContextQuestion
from owndraft.core.errors import ModelOutputError
from owndraft.llm.parser import parse_model_json


def test_parser_accepts_json_inside_markdown_fence():
    raw = (
        '```json\n{"id":"q1","question":"실제 시간이 얼마나 줄었나요?",'
        '"target_gap":"metric","expected_answer_type":"number"}\n```'
    )
    parsed = parse_model_json(raw, ContextQuestion)
    assert parsed.id == "q1"


def test_parser_accepts_raw_json_without_fence():
    raw = '{"id":"q2","question":"목표가 무엇인가요?","target_gap":"goal","expected_answer_type":"goal"}'
    parsed = parse_model_json(raw, ContextQuestion)
    assert parsed.target_gap == "goal"


def test_parser_rejects_non_json_after_one_local_parse_attempt():
    with pytest.raises(ModelOutputError):
        parse_model_json("결과는 다음과 같습니다.", ContextQuestion)


def test_parser_rejects_schema_mismatch_with_distinct_error_code():
    with pytest.raises(ModelOutputError) as exc_info:
        parse_model_json('{"unexpected": true}', ContextQuestion)

    assert exc_info.value.code == "model_schema_mismatch"


def test_parser_rejects_empty_content():
    with pytest.raises(ModelOutputError) as exc_info:
        parse_model_json("", ContextQuestion)

    assert exc_info.value.code == "model_output_unparseable"
