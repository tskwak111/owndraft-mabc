"""Acceptance gate: deterministic decision over preservation and critics.

The repair prompt receives only machine-readable issue codes, affected spans,
locked values, and the candidate text — never vague goals like "make it more
human".
"""

import time
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel

from owndraft.contracts.stage1 import CriticScore, PreservationReport


class WorkflowState(StrEnum):
    VALIDATE = "validate"
    DETERMINISTIC_CLAIMS = "deterministic_claims"
    MODEL_CLAIMS = "model_claims"
    PATTERNS = "patterns"
    VOICE_PROFILE = "voice_profile"
    CONTEXT_GAP = "context_gap"
    REWRITE_PLAN = "rewrite_plan"
    CANDIDATE = "candidate"
    CRITICS = "critics"
    ACCEPTANCE_GATE = "acceptance_gate"
    REPAIR = "repair"


@dataclass(frozen=True)
class TraceEvent:
    state: WorkflowState
    latency_ms: int
    input_chars: int
    output_chars: int
    success: bool
    error_code: str | None


@dataclass(frozen=True)
class CriticBundle:
    fact: CriticScore
    fidelity: CriticScore
    voice: CriticScore
    naturalness: CriticScore


class RepairInstruction(BaseModel):
    code: str
    span_id: str | None = None
    claim_id: str | None = None
    detail: str = ""


class AcceptanceDecision(BaseModel):
    passed: bool
    repair_instructions: list[RepairInstruction]


def collect_machine_readable_issues(
    report: PreservationReport,
    critics: CriticBundle,
) -> list[RepairInstruction]:
    instructions: list[RepairInstruction] = [
        RepairInstruction(
            code=issue.code,
            claim_id=issue.claim_id,
            detail=issue.detail,
        )
        for issue in report.issues
    ]
    for critic in (critics.fact, critics.fidelity, critics.voice, critics.naturalness):
        for issue in critic.issues:
            instructions.append(RepairInstruction(code=f"{critic.critic}_issue", detail=issue))
    return instructions


def decide_acceptance(report: PreservationReport, critics: CriticBundle) -> AcceptanceDecision:
    """Fixed deterministic acceptance criteria from the design spec."""

    passed = (
        report.passed
        and critics.fact.new_claim_count == 0
        and critics.fact.severe_error_count == 0
        and critics.fidelity.severe_error_count == 0
        and critics.naturalness.high_severity_unresolved == 0
        and (
            critics.voice.skipped
            or (critics.voice.constraint_match is not None and critics.voice.constraint_match >= 0.90)
        )
    )
    return AcceptanceDecision(
        passed=passed,
        repair_instructions=collect_machine_readable_issues(report, critics),
    )


def trace_event(state: WorkflowState, started: float, error: Exception | None = None) -> TraceEvent:
    latency_ms = int((time.perf_counter() - started) * 1000)
    return TraceEvent(
        state=state,
        latency_ms=latency_ms,
        input_chars=0,
        output_chars=0,
        success=error is None,
        error_code=getattr(error, "code", type(error).__name__ if error else None),
    )


def issue_summary_for_prompt(instructions: list[RepairInstruction]) -> list[dict[str, str]]:
    return [instruction.model_dump() for instruction in instructions]
