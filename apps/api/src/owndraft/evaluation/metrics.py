"""Evaluation metrics for the 20-case stage 1 regression suite."""

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Per-case metric bundle.

    `passed` is deliberately strict: a case fails immediately when locked fact
    preservation drops below 100% or any unsupported new claim appears,
    regardless of judge scores.
    """

    locked_fact_preservation: float = Field(ge=0.0, le=1.0)
    new_claim_rate: float = Field(ge=0.0)
    semantic_fidelity: float = Field(ge=1.0, le=5.0)
    pattern_reduction: float = Field(ge=0.0, le=1.0)
    voice_constraint_match: float | None = Field(default=None, ge=0.0, le=1.0)
    severe_locked_fact_errors: int = Field(default=0, ge=0)

    @property
    def passed(self) -> bool:
        return (
            self.locked_fact_preservation >= 1.0
            and self.new_claim_rate == 0.0
            and self.severe_locked_fact_errors == 0
        )


def aggregate_results(results: list[EvaluationResult]) -> dict[str, float | int]:
    """Compute stage 1 summary statistics over all case results."""

    total = len(results)
    if total == 0:
        return {
            "total_cases": 0,
            "average_pattern_reduction": 0.0,
            "average_semantic_fidelity": 0.0,
            "voice_mode_cases": 0,
            "voice_mode_average_constraint_match": 0.0,
        }
    voice_matches = [
        result.voice_constraint_match
        for result in results
        if result.voice_constraint_match is not None
    ]
    return {
        "total_cases": total,
        "average_pattern_reduction": sum(r.pattern_reduction for r in results) / total,
        "average_semantic_fidelity": sum(r.semantic_fidelity for r in results) / total,
        "voice_mode_cases": len(voice_matches),
        "voice_mode_average_constraint_match": (
            sum(voice_matches) / len(voice_matches) if voice_matches else 0.0
        ),
    }
