"""Deterministic Claim Locker: extracts factual anchors before any LLM call."""

import re

from owndraft.contracts.stage1 import Claim, Stage1Request
from owndraft.text.normalization import normalize_for_comparison

_URL_RE = re.compile(r"https?://[^\s)\]}>'\"<가-힣ㄱ-ㅎㅏ-ㅣ]+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_QUOTE_RES = [
    re.compile(r'"([^"\n]{2,120})"'),
    re.compile(r"“([^”\n]{2,120})”"),
    re.compile(r"『([^』\n]{2,120})』|「([^「\n]{2,120})」"),
]
_DATE_RES = [
    re.compile(r"\d{4}\s*년\s*\d{1,2}\s*월\s*\d{1,2}\s*일"),
    re.compile(r"\d{1,2}\s*월\s*\d{1,2}\s*일"),
    re.compile(r"\d{4}\s*년"),
    re.compile(r"(?:지난|이번|다음|다음)주\s*[가-힣]요일"),
    re.compile(r"[가-힣]요일(?:까지|마다|에)?"),
    re.compile(r"(?:지난|이번|다음)\s*(?:달|주|주말|해)"),
]
_TIME_RE = re.compile(r"(?:오전|오후)?\s*\d{1,2}\s*시(?:\s*\d{1,2}\s*분)?(?:\s*\d{1,2}\s*초)?")
_NUMBER_RE = re.compile(
    r"\d[\d,]*(?:\.\d+)?"
    r"(?:\s*만 ?원|억 ?원|천 ?원|백만 ?원|원|달러|유로|엔|퍼센트|%|배|"
    r"개|명|건|회|번|분|시간|초|일간|일|주일|주|개월|달|년|ms|km|KM|Km|kg|KG|mm|cm|g|m|"
    r"GB|MB|KB|TB|GiB|Mib|GHz|MHz|Hz|°C|℃|도|포인트|점|석|층|페이지|장)"
)
_NEGATION_RE = re.compile(
    r"(?:아니[다라고며]|아닙니다|[가-힣]지 않[는았으며다]|[가-힣]질 않[는았으며다]"
    r"|없[다습니다어었]|못[하했하는]|금지|불가능)"
)
_CONDITIONAL_RE = re.compile(r"(경우|때만|제외|만약|단[,，.]|필수 조건|조건)")


def _claim_type_for_number(value: str) -> str:
    return "number"


def _make_claim(
    start: int,
    end: int,
    claim_type: str,
    evidence_type: str,
    source_text: str,
) -> Claim:
    return Claim(
        id=f"det_{start:05d}_{end:05d}",
        claim_type=claim_type,
        source_text=source_text,
        normalized_value=normalize_for_comparison(source_text),
        start=start,
        end=end,
        locked=True,
        evidence_type=evidence_type,
    )


def _find_all(pattern: re.Pattern[str], text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in pattern.finditer(text)]


def _add_claims(
    collected: list[Claim],
    bounds: list[tuple[int, int]],
    text: str,
    claim_type: str,
    evidence_type: str,
) -> None:
    for start, end in bounds:
        collected.append(_make_claim(start, end, claim_type, evidence_type, text[start:end]))


def _dedupe(collected: list[Claim]) -> list[Claim]:
    """Remove exact duplicates; allow overlaps only across different types."""
    seen_exact: set[tuple[int, int, str]] = set()
    exact_unique: list[Claim] = []
    for claim in collected:
        key = (claim.start, claim.end, claim.claim_type)
        if key in seen_exact:
            continue
        seen_exact.add(key)
        exact_unique.append(claim)

    kept: list[Claim] = []
    occupied: dict[str, list[tuple[int, int]]] = {}
    for claim in sorted(exact_unique, key=lambda c: (c.start, -(c.end - c.start))):
        ranges = occupied.setdefault(claim.claim_type, [])
        if any(not (claim.end <= s or claim.start >= e) for s, e in ranges):
            continue
        ranges.append((claim.start, claim.end))
        kept.append(claim)
    return kept


def extract_deterministic_claims(request: Stage1Request) -> list[Claim]:
    """Extract locked anchors with original-text offsets, in fixed order:

    locked_phrases → URLs → markdown links → quotes → dates → times →
    numbers with units → negations → conditionals.
    """

    text = request.text
    collected: list[Claim] = []

    # 1. user locked phrases (longest first so "Solar Pro" wins over partial)
    for phrase in sorted(request.locked_phrases, key=len, reverse=True):
        if not phrase.strip():
            continue
        _add_claims(
            collected,
            [(m.start(), m.end()) for m in re.finditer(re.escape(phrase.strip()), text)],
            text,
            claim_type="locked_phrase",
            evidence_type="user_locked",
        )

    # 2. URLs
    _add_claims(collected, _find_all(_URL_RE, text), text, "url", "link")

    # 2b. email addresses
    _add_claims(collected, _find_all(_EMAIL_RE, text), text, "email", "link")

    # 3. Markdown links (lock the target URL)
    for match in _MARKDOWN_LINK_RE.finditer(text):
        url_start = match.start(2)
        collected.append(
            _make_claim(url_start, match.end(2), "markdown_link", "link", match.group(2))
        )

    # 4. quoted spans
    for quote_re in _QUOTE_RES:
        for match in quote_re.finditer(text):
            group = next(group for group in match.groups() if group is not None)
            start = text.index(group, match.start())
            collected.append(_make_claim(start, start + len(group), "quote", "direct_quote", group))

    # 5. dates and times
    _add_claims(collected, _find_all(_DATE_RES[0], text), text, "date", "fact_value")
    for date_re in _DATE_RES[1:]:
        _add_claims(collected, _find_all(date_re, text), text, "date", "fact_value")

    # 6. times
    _add_claims(collected, _find_all(_TIME_RE, text), text, "time", "fact_value")

    # 7. numbers with units, currency, percentages
    _add_claims(collected, _find_all(_NUMBER_RE, text), text, _claim_type_for_number(""), "fact_value")

    # 8. explicit negations
    _add_claims(collected, _find_all(_NEGATION_RE, text), text, "negation", "polarity")

    # 9. conditionals
    _add_claims(collected, _find_all(_CONDITIONAL_RE, text), text, "conditional", "condition")

    return _dedupe(collected)
