"""Sentence/paragraph segmentation that preserves original text offsets.

Spans always satisfy `text[span.start:span.end] == span.text` so claims and
findings can reference exact source positions.
"""

import re

from pydantic import BaseModel

_SENTENCE_END = re.compile(r"[.!?]")
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


class TextSpan(BaseModel):
    id: str
    start: int
    end: int
    text: str


def _sentence_end_positions(paragraph: str) -> list[int]:
    ends: list[int] = []
    position = 0
    while True:
        match = _SENTENCE_END.search(paragraph, position)
        if match is None:
            return ends
        end = match.end()
        if (
            paragraph[match.start()] == "."
            and 0 < match.start()
            and paragraph[match.start() - 1].isdigit()
            and end < len(paragraph)
            and paragraph[end].isdigit()
        ):
            # decimal numbers such as "3.5" must not split a sentence
            position = end
            continue
        ends.append(end)
        position = end


def _raw_sentence_bounds(paragraph: str, offset: int) -> list[tuple[int, int]]:
    bounds: list[tuple[int, int]] = []
    start = 0
    for end in _sentence_end_positions(paragraph):
        bounds.append((offset + start, offset + end))
        start = end
    tail = paragraph[start:]
    if tail.strip():
        leading = len(tail) - len(tail.lstrip())
        trailing = len(tail) - len(tail.rstrip())
        bounds.append((offset + start + leading, offset + len(paragraph) - trailing))
    return bounds


def _paragraph_chunks(text: str) -> list[tuple[int, str]]:
    """Return (offset, chunk) pairs where offset is exact position in `text`."""
    chunks: list[tuple[int, str]] = []
    cursor = 0
    for match in _PARAGRAPH_BREAK.finditer(text):
        chunks.append((cursor, text[cursor : match.start()]))
        cursor = match.end()
    chunks.append((cursor, text[cursor:]))
    return chunks


def segment_text(text: str) -> list[TextSpan]:
    """Split at paragraph breaks or sentence-ending punctuation.

    Empty spans are discarded and IDs are stable (`s_0001`, ...) in source order.
    """

    candidates: list[tuple[int, int]] = []
    for chunk_offset, chunk in _paragraph_chunks(text):
        for start, end in _raw_sentence_bounds(chunk, chunk_offset):
            segment = text[start:end]
            leading = len(segment) - len(segment.lstrip())
            trailing = len(segment) - len(segment.rstrip())
            adjusted = (start + leading, end - trailing)
            if adjusted[0] < adjusted[1] and text[adjusted[0] : adjusted[1]].strip():
                candidates.append(adjusted)

    return [
        TextSpan(id=f"s_{index:04d}", start=start, end=end, text=text[start:end])
        for index, (start, end) in enumerate(candidates, start=1)
    ]
