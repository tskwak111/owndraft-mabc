"""Deterministic regex-based scanning of Korean AI writing patterns."""

import re

from pydantic import BaseModel, Field

from owndraft.contracts.stage1 import PatternFinding
from owndraft.patterns.catalog import PatternRule
from owndraft.text.segmentation import TextSpan


class CompiledPattern(BaseModel):
    code: str
    severity: str = Field(pattern="^(low|medium|high)$")
    action: str = Field(pattern="^(keep|rewrite|delete|ask)$")
    reason: str
    regexes: list[re.Pattern[str]]

    model_config = {"arbitrary_types_allowed": True}


def compile_rules(rules: list[PatternRule]) -> list[CompiledPattern]:
    compiled: list[CompiledPattern] = []
    for rule in rules:
        compiled.append(
            CompiledPattern(
                code=rule.code,
                severity=rule.severity,
                action=rule.default_action,
                reason=rule.description_ko,
                regexes=[re.compile(pattern) for pattern in rule.regexes],
            )
        )
    return compiled


def scan_deterministic_patterns(
    spans: list[TextSpan],
    rules: list[PatternRule],
) -> list[PatternFinding]:
    """Scan spans with high-precision regexes only.

    Findings are deduplicated by (span_id, pattern_code) and preserve source
    order. Contextual rules carry no regexes and are handled by the LLM stage.
    """

    findings: list[PatternFinding] = []
    seen: set[tuple[str, str]] = set()
    for span in spans:
        for rule in compile_rules(rules):
            key = (span.id, rule.code)
            if key in seen:
                continue
            if any(regex.search(span.text) for regex in rule.regexes):
                seen.add(key)
                findings.append(
                    PatternFinding(
                        span_id=span.id,
                        pattern_code=rule.code,
                        severity=rule.severity,  # type: ignore[arg-type]
                        reason=rule.reason,
                        action=rule.action,  # type: ignore[arg-type]
                    )
                )
    return findings
