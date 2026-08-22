"""Comparison-only text normalization.

The normalized value is never used for user-visible output offsets; it exists
so claims can be matched across formatting differences.
"""

import re
import unicodedata


def normalize_for_comparison(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\s+", " ", normalized).strip()
