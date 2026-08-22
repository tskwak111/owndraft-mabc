"""Preservation verification: deterministic checks over locked claims."""

import re

from owndraft.contracts.stage1 import Claim, PreservationIssue, PreservationReport
from owndraft.text.normalization import normalize_for_comparison

_NUMBER_CORE_RE = re.compile(r"\d[\d,.]*")
_UNIT_RE = re.compile(r"[가-힣A-Za-z%°℃]+")


def _number_parts(value: str) -> tuple[str | None, str]:
    core = _NUMBER_CORE_RE.search(value)
    numeric = core.group() if core else None
    unit = value[core.end() :] if core else ""
    return (numeric.strip(",.") if numeric else None, unit.strip())


def _numeric_present(numeric: str, haystack: str) -> bool:
    """Match a number with or without thousands separators on both sides."""

    if numeric in haystack:
        return True
    compact_numeric = numeric.replace(",", "")
    compact_haystack = haystack.replace(",", "")
    return compact_numeric in compact_haystack


def _check_number(claim: Claim, normalized_rewritten: str) -> PreservationIssue | None:
    if claim.normalized_value in normalized_rewritten:
        return None
    numeric, unit = _number_parts(claim.normalized_value)
    if numeric is None or not _numeric_present(numeric, normalized_rewritten):
        return PreservationIssue(
            code="locked_value_missing", severity="high", claim_id=claim.id
        )
    rewritten_unit = ""
    for match in _NUMBER_CORE_RE.finditer(normalized_rewritten):
        core_value = match.group().strip(",.")
        if core_value == numeric or core_value.replace(",", "") == numeric.replace(",", ""):
            after = normalized_rewritten[match.end() :]
            unit_match = _UNIT_RE.match(after)
            rewritten_unit = unit_match.group() if unit_match else ""
            break
    if unit and not rewritten_unit.startswith(unit[:1]):
        return PreservationIssue(
            code="unit_changed", severity="high", claim_id=claim.id
        )
    return None


def verify_preservation(
    claims: list[Claim],
    rewritten_text: str,
    model_claims: list[Claim] | None = None,
    unsupported_new_claims: list[Claim] | None = None,
) -> PreservationReport:
    """Deterministically verify every locked claim survived the rewrite.

    A case passes only when zero high-severity issues remain and no
    unsupported new claims were reported by critics.
    """

    normalized_rewritten = normalize_for_comparison(rewritten_text)
    issues: list[PreservationIssue] = []
    preserved = 0

    for claim in claims:
        issue: PreservationIssue | None = None
        if claim.claim_type in {"date", "time", "number"}:
            issue = _check_number(claim, normalized_rewritten)
        elif claim.claim_type in {"url", "markdown_link", "email"}:
            if claim.normalized_value not in normalized_rewritten:
                issue = PreservationIssue(
                    code="source_changed", severity="high", claim_id=claim.id
                )
        elif claim.claim_type == "quote":
            if claim.normalized_value not in normalized_rewritten:
                issue = PreservationIssue(
                    code="quote_changed", severity="high", claim_id=claim.id
                )
        elif claim.claim_type == "negation" or claim.claim_type == "conditional":
            if claim.normalized_value not in normalized_rewritten:
                issue = PreservationIssue(
                    code="polarity_changed", severity="high", claim_id=claim.id
                )
        else:  # locked_phrase and any other anchor type
            if claim.normalized_value not in normalized_rewritten:
                issue = PreservationIssue(
                    code="locked_value_missing", severity="high", claim_id=claim.id
                )

        if issue is None:
            preserved += 1
        else:
            issues.append(issue)

    new_claims = len(unsupported_new_claims or [])
    passed = all(issue.severity != "high" for issue in issues) and new_claims == 0

    return PreservationReport(
        passed=passed,
        issues=issues,
        locked_total=len(claims),
        preserved_locked=preserved,
        new_claim_count=new_claims,
    )
