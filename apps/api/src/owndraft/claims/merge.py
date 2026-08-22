"""Merge deterministic and model-proposed claims with offset validation."""

from owndraft.contracts.stage1 import Claim


def merge_model_claims(
    original_text: str,
    deterministic: list[Claim],
    model_claims: list[Claim],
) -> list[Claim]:
    """Merge claims; model offsets are trusted only when they match source text.

    Deterministic claims win on identical keys. Result is ordered by position
    and renumbered deterministically as clm_0001, clm_0002, ...
    """

    valid_model_claims = [
        claim
        for claim in model_claims
        if 0 <= claim.start < claim.end <= len(original_text)
        and original_text[claim.start : claim.end] == claim.source_text
    ]
    by_key = {
        (claim.start, claim.end, claim.claim_type, claim.normalized_value): claim
        for claim in valid_model_claims
    }
    for claim in deterministic:
        by_key[(claim.start, claim.end, claim.claim_type, claim.normalized_value)] = claim
    ordered = sorted(by_key.values(), key=lambda claim: (claim.start, claim.end, claim.claim_type))
    return [
        claim.model_copy(update={"id": f"clm_{index:04d}"})
        for index, claim in enumerate(ordered, start=1)
    ]
