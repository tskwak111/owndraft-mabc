from owndraft.claims.locker import extract_deterministic_claims
from owndraft.claims.merge import merge_model_claims
from owndraft.contracts.stage1 import Claim, EditMode, Stage1Request

ORIGINAL = 'Solar로 40분 걸리던 정리가 5분으로 줄었다.'


def _request() -> Stage1Request:
    return Stage1Request(
        text=ORIGINAL,
        purpose="블로그",
        audience="독자들",
        edit_mode=EditMode.MINIMAL,
        locked_phrases=["Solar"],
    )


def test_merge_rejects_model_claims_with_wrong_offsets():
    deterministic = extract_deterministic_claims(_request())
    bogus = Claim(
        id="m_0001",
        claim_type="number",
        source_text="40분",
        normalized_value="40분",
        start=0,
        end=2,
        locked=True,
        evidence_type="fact_value",
    )
    merged = merge_model_claims(ORIGINAL, deterministic, [bogus])

    assert all(claim.id != "m_0001" for claim in merged)
    assert ORIGINAL[0:2] != "40분"


def test_merge_accepts_valid_model_claims_and_dedupes():
    deterministic = extract_deterministic_claims(_request())
    valid_duplicate = Claim(
        id="m_0001",
        claim_type="number",
        source_text="40분",
        normalized_value="40분",
        start=ORIGINAL.index("40분"),
        end=ORIGINAL.index("40분") + len("40분"),
        locked=True,
        evidence_type="model_found",
    )
    merged = merge_model_claims(ORIGINAL, deterministic, [valid_duplicate])

    keys = [(claim.start, claim.end, claim.claim_type, claim.normalized_value) for claim in merged]
    assert len(keys) == len(set(keys))
    assert [claim.id for claim in merged] == [
        f"clm_{index:04d}" for index in range(1, len(merged) + 1)
    ]
    # deterministic evidence wins on identical key
    winner = next(claim for claim in merged if claim.source_text == "40분")
    assert winner.evidence_type == "fact_value"
