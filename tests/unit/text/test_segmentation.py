from owndraft.text.segmentation import segment_text


def test_segment_text_preserves_original_offsets():
    text = "첫 문장입니다.\n두 번째 문장입니다!"
    spans = segment_text(text)

    assert [span.text for span in spans] == ["첫 문장입니다.", "두 번째 문장입니다!"]
    assert all(text[span.start : span.end] == span.text for span in spans)
    assert [span.id for span in spans] == ["s_0001", "s_0002"]


def test_segment_text_splits_on_korean_sentence_punctuation():
    text = "첫 번째 내용이다? 네. 두 번째 내용이다!"
    spans = segment_text(text)

    assert [span.text for span in spans] == ["첫 번째 내용이다?", "네.", "두 번째 내용이다!"]
    assert all(text[span.start : span.end] == span.text for span in spans)


def test_segment_text_discards_empty_spans():
    text = "문장 하나.\n\n   \n또 하나."
    spans = segment_text(text)

    assert [span.text for span in spans] == ["문장 하나.", "또 하나."]


def test_segment_text_ids_are_stable_and_ordered():
    text = "하나. 둘.\n셋. 넷. 다섯."
    spans = segment_text(text)

    assert [span.id for span in spans] == [f"s_{i:04d}" for i in range(1, len(spans) + 1)]
