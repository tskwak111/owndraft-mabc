from owndraft.contracts.stage1 import ContextQuestion
from owndraft.voice.context_gap import select_context_questions


def test_context_questions_are_unique_specific_and_capped_at_three():
    candidates = [
        ContextQuestion(
            id="q1",
            question="줄어든 시간이 있나요?",
            target_gap="metric",
            expected_answer_type="number",
        ),
        ContextQuestion(
            id="q2",
            question="실제 사례 한 가지가 있나요?",
            target_gap="experience",
            expected_answer_type="experience",
        ),
        ContextQuestion(
            id="q3",
            question="독자가 무엇을 해보길 바라나요?",
            target_gap="goal",
            expected_answer_type="goal",
        ),
        ContextQuestion(
            id="q4",
            question="더 구체적으로 말해 주세요.",
            target_gap="vague",
            expected_answer_type="opinion",
        ),
    ]

    selected = select_context_questions(candidates, original_text="효율이 좋아졌다.")

    assert [q.id for q in selected] == ["q1", "q2", "q3"]
    assert all("더 구체적으로" not in q.question for q in selected)


def test_duplicate_target_gap_is_dropped():
    candidates = [
        ContextQuestion(
            id="q1",
            question="줄어든 시간이 있나요?",
            target_gap="metric",
            expected_answer_type="number",
        ),
        ContextQuestion(
            id="q2",
            question="절약된 비용이 얼마인가요?",
            target_gap="metric",
            expected_answer_type="number",
        ),
    ]

    selected = select_context_questions(candidates, original_text="효율이 좋아졌다.")

    assert [q.id for q in selected] == ["q1"]


def test_question_already_answered_in_original_is_rejected():
    candidates = [
        ContextQuestion(
            id="q1",
            question="40분에서 얼마나 더 줄였나요?",
            target_gap="metric",
            expected_answer_type="number",
        ),
        ContextQuestion(
            id="q2",
            question="독자가 무엇을 해보길 바라나요?",
            target_gap="goal",
            expected_answer_type="goal",
        ),
    ]
    original = "회의록 정리가 40분에서 5분으로 줄었다."

    selected = select_context_questions(candidates, original_text=original)

    assert [q.id for q in selected] == ["q2"]


def test_more_than_three_valid_candidates_ranked_then_capped():
    candidates = [
        ContextQuestion(
            id=f"q{i}",
            question=f"구체적 후보 {i}번에 대해 답해 줄 수 있나요?",
            target_gap=f"gap_{i}",
            expected_answer_type=answer_type,
        )
        for i, answer_type in enumerate(
            ["opinion", "source", "number", "experience", "goal"], start=1
        )
    ]

    selected = select_context_questions(candidates, original_text="충분히 긴 원문 텍스트입니다.")

    assert len(selected) == 3
    # ranking decides survival; presentation keeps candidate input order
    assert [q.expected_answer_type for q in selected] == ["source", "number", "experience"]
