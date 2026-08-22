"""Parallel critics: fact, fidelity, voice, naturalness."""

import asyncio

from owndraft.contracts.stage1 import Claim, CriticScore, VoiceProfile
from owndraft.llm.gateway import ModelGateway
from owndraft.prompts.builder import build_operation_prompt
from owndraft.workflow.gates import CriticBundle


async def _call_critic(
    gateway: ModelGateway,
    *,
    operation: str,
    payload: dict[str, object],
) -> CriticScore:
    prompt = build_operation_prompt(operation, payload=payload)
    return await gateway.complete_json(
        operation=operation,
        system_prompt=prompt.system_prompt,
        user_prompt=prompt.user_prompt,
        response_model=CriticScore,
    )


async def run_fact_critic(
    gateway: ModelGateway,
    original_text: str,
    candidate_text: str,
    claims: list[Claim],
) -> CriticScore:
    locked_values = [
        {"claim_type": claim.claim_type, "normalized_value": claim.normalized_value}
        for claim in claims
        if claim.locked
    ]
    return await _call_critic(
        gateway,
        operation="critic_fact",
        payload={
            "original_text": original_text,
            "candidate_text": candidate_text,
            "locked_claims": locked_values,
        },
    )


async def run_fidelity_critic(
    gateway: ModelGateway,
    original_text: str,
    candidate_text: str,
    core_claims: list[Claim],
) -> CriticScore:
    core_values = [claim.normalized_value for claim in core_claims]
    return await _call_critic(
        gateway,
        operation="critic_fidelity",
        payload={
            "original_text": original_text,
            "candidate_text": candidate_text,
            "core_claim_values": core_values,
        },
    )


async def run_voice_critic(
    gateway: ModelGateway,
    candidate_text: str,
    voice_profile: VoiceProfile,
    purpose: str,
) -> CriticScore:
    return await _call_critic(
        gateway,
        operation="critic_voice",
        payload={
            "candidate_text": candidate_text,
            "voice_profile": voice_profile.model_dump(),
            "purpose": purpose,
        },
    )


def skipped_voice_critic() -> CriticScore:
    """Voice critic result when samples are absent; never lowers the score."""

    return CriticScore(critic="voice", score=0.0, skipped=True, passed=True)


async def run_naturalness_critic(
    gateway: ModelGateway,
    candidate_text: str,
    detected_pattern_codes: list[str],
) -> CriticScore:
    return await _call_critic(
        gateway,
        operation="critic_naturalness",
        payload={
            "candidate_text": candidate_text,
            "detected_pattern_codes": detected_pattern_codes,
        },
    )


async def run_all_critics(
    gateway: ModelGateway,
    *,
    original_text: str,
    candidate_text: str,
    claims: list[Claim],
    voice_profile: VoiceProfile,
    purpose: str,
    pattern_codes: list[str],
    voice_applicable: bool,
) -> CriticBundle:
    fact, fidelity, voice, naturalness = await asyncio.gather(
        run_fact_critic(gateway, original_text, candidate_text, claims),
        run_fidelity_critic(gateway, original_text, candidate_text, claims),
        (
            run_voice_critic(gateway, candidate_text, voice_profile, purpose)
            if voice_applicable
            else asyncio.sleep(0, result=skipped_voice_critic())
        ),
        run_naturalness_critic(gateway, candidate_text, pattern_codes),
    )
    return CriticBundle(
        fact=fact, fidelity=fidelity, voice=voice, naturalness=naturalness
    )
