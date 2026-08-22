"""Stage 1 orchestration: explicit state machine with a one-repair gate."""

import asyncio
import time
import uuid

from owndraft.claims.locker import extract_deterministic_claims
from owndraft.claims.merge import merge_model_claims
from owndraft.claims.verifier import verify_preservation
from owndraft.contracts.stage1 import (
    CandidateDraft,
    ClaimBundle,
    EditMode,
    PatternBundle,
    PatternFinding,
    QuestionBundle,
    RewritePlan,
    Stage1Request,
    Stage1Result,
    VoiceProfile,
)
from owndraft.core.settings import Settings
from owndraft.llm.gateway import ModelGateway
from owndraft.patterns.catalog import load_pattern_catalog
from owndraft.patterns.scanner import scan_deterministic_patterns
from owndraft.prompts.builder import build_operation_prompt
from owndraft.text.segmentation import segment_text
from owndraft.voice.context_gap import select_context_questions
from owndraft.voice.profiler import fallback_voice_profile, validate_voice_profile
from owndraft.workflow.critics import run_all_critics
from owndraft.workflow.gates import (
    TraceEvent,
    WorkflowState,
    decide_acceptance,
    trace_event,
)


class Stage1Workflow:
    """Runs the fixed stage 1 pipeline against any ModelGateway.

    State order is fixed:
    validate → deterministic_claims → model_claims → patterns → voice_profile
    → context_gap → needs_context | rewrite_plan → candidate → critics
    → acceptance_gate → completed | one repair → critics → completed | blocked.
    """

    def __init__(self, gateway: ModelGateway, settings: Settings | None = None) -> None:
        self._gateway = gateway
        self._settings = settings or Settings()
        self.last_trace_events: list[TraceEvent] = []

    async def _call(
        self,
        operation: str,
        payload: dict[str, object],
        response_model: type,
    ):
        prompt = build_operation_prompt(operation, payload=payload)
        return await self._gateway.complete_json(
            operation=operation,
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            response_model=response_model,
        )

    async def run(
        self,
        request: Stage1Request,
        context_answers: dict[str, str] | None = None,
    ) -> Stage1Result:
        trace_id = uuid.uuid4().hex
        events: list = []
        self.last_trace_events = events

        # validate
        started = time.perf_counter()
        events.append(trace_event(WorkflowState.VALIDATE, started))

        # deterministic_claims
        started = time.perf_counter()
        deterministic_claims = extract_deterministic_claims(request)
        events.append(
            trace_event(WorkflowState.DETERMINISTIC_CLAIMS, started, input_chars=len(request.text))
        )

        # model_claims
        try:
            bundle: ClaimBundle = await self._call(
                "extract_claims",
                {"text": request.text, "locked_phrases": request.locked_phrases},
                ClaimBundle,
            )
            claims = merge_model_claims(request.text, deterministic_claims, bundle.claims)
        except Exception as error:
            events.append(trace_event(WorkflowState.MODEL_CLAIMS, time.perf_counter(), error))
            raise
        events.append(
            trace_event(WorkflowState.MODEL_CLAIMS, time.perf_counter(), output_chars=sum(len(c.source_text) for c in claims))
        )

        # deterministic_patterns + model_patterns (parallel)
        started = time.perf_counter()
        spans = segment_text(request.text)
        catalog = load_pattern_catalog()
        det_findings, pattern_bundle = await asyncio.gather(
            asyncio.sleep(0, result=scan_deterministic_patterns(spans, catalog)),
            self._call("scan_patterns", {"spans": [span.model_dump() for span in spans]}, PatternBundle),
        )
        # model findings referencing hallucinated spans are dropped
        known_span_ids = {span.id for span in spans}
        combined: dict[tuple[str, str], PatternFinding] = {
            (finding.span_id, finding.pattern_code): finding
            for finding in [*det_findings, *pattern_bundle.findings]
            if finding.span_id in known_span_ids
        }
        diagnosis = list(combined.values())
        events.append(
            trace_event(WorkflowState.PATTERNS, started, input_chars=len(request.text), output_chars=len(diagnosis))
        )

        # voice_profile
        started = time.perf_counter()
        if request.voice_sample_confidence != "none":
            profile_raw = await self._call(
                "profile_voice",
                {"samples": request.voice_samples, "purpose": request.purpose},
                VoiceProfile,
            )
            voice_profile: VoiceProfile = validate_voice_profile(profile_raw.model_dump())
        else:
            voice_profile = fallback_voice_profile(request.voice_samples)
        events.append(trace_event(WorkflowState.VOICE_PROFILE, started))

        # context_gap
        started = time.perf_counter()
        question_bundle: QuestionBundle = await self._call(
            "find_context_gaps",
            {
                "text": request.text,
                "purpose": request.purpose,
                "audience": request.audience,
                "diagnosis": [
                    {"code": finding.pattern_code, "reason": finding.reason}
                    for finding in diagnosis[:10]
                ],
                "locked_values": sorted({claim.normalized_value for claim in claims}),
            },
            QuestionBundle,
        )
        questions = select_context_questions(question_bundle.questions, request.text)
        events.append(
            trace_event(WorkflowState.CONTEXT_GAP, started, input_chars=len(request.text), output_chars=len(questions))
        )

        if questions and not context_answers:
            return Stage1Result(
                status="needs_context",
                diagnosis=diagnosis,
                questions=questions,
                rewritten_text=None,
                changes=[],
                preservation=None,
                trace_id=trace_id,
            )

        answers = context_answers or {}
        started = time.perf_counter()
        locked_values = sorted({claim.normalized_value for claim in claims})

        plan: RewritePlan = await self._call(
            "plan_rewrite",
            {
                "text": request.text,
                "purpose": request.purpose,
                "audience": request.audience,
                "edit_mode": str(request.effective_edit_mode.value),
                "findings": [{"span_id": f.span_id, "code": f.pattern_code} for f in diagnosis],
                "locked_values": sorted({claim.normalized_value for claim in claims}),
                "user_answers": answers,
            },
            RewritePlan,
        )
        events.append(trace_event(WorkflowState.REWRITE_PLAN, started))

        async def _produce(
            operation: str, extra_issues: list[dict[str, str]] | None = None
        ) -> CandidateDraft:
            return await self._call(
                operation,
                {
                    "text": request.text,
                    "edit_mode": str(request.effective_edit_mode.value),
                    "locked_values": locked_values,
                    "plan_goals": plan.goals,
                    "user_answers": answers,
                    **({"issues": extra_issues} if extra_issues is not None else {}),
                },
                CandidateDraft,
            )

        started = time.perf_counter()
        candidate = await _produce("write_candidate")
        events.append(
            trace_event(WorkflowState.CANDIDATE, started, input_chars=len(request.text), output_chars=len(candidate.rewritten_text))
        )
        repair_attempts = 0
        preservation = verify_preservation(claims, candidate.rewritten_text)

        for attempt in range(self._settings.max_repair_attempts + 1):
            started = time.perf_counter()
            critics = await run_all_critics(
                self._gateway,
                original_text=request.text,
                candidate_text=candidate.rewritten_text,
                claims=claims,
                voice_profile=voice_profile,
                purpose=request.purpose,
                pattern_codes=[finding.pattern_code for finding in diagnosis],
                voice_applicable=request.effective_edit_mode is EditMode.VOICE,
            )
            events.append(trace_event(WorkflowState.CRITICS, started))
            started = time.perf_counter()
            decision = decide_acceptance(preservation, critics)
            events.append(trace_event(WorkflowState.ACCEPTANCE_GATE, started))
            if decision.passed:
                break
            if attempt >= self._settings.max_repair_attempts:
                preservation = preservation.model_copy(update={"repair_attempts": repair_attempts})
                return Stage1Result(
                    status="blocked",
                    diagnosis=diagnosis,
                    questions=[],
                    rewritten_text=None,
                    # the candidate was discarded; do not surface its reasons
                    changes=[],
                    preservation=preservation,
                    trace_id=trace_id,
                )
            repair_instructions = [
                instruction.model_dump() for instruction in decision.repair_instructions
            ]
            candidate = await _produce("repair_candidate", repair_instructions)
            repair_attempts += 1
            preservation = verify_preservation(claims, candidate.rewritten_text)
            events.append(
                trace_event(WorkflowState.REPAIR, time.perf_counter(), output_chars=len(candidate.rewritten_text))
            )

        preservation = preservation.model_copy(update={"repair_attempts": repair_attempts})
        return Stage1Result(
            status="completed",
            diagnosis=diagnosis,
            questions=[],
            rewritten_text=candidate.rewritten_text,
            changes=candidate.change_reasons,
            preservation=preservation,
            trace_id=trace_id,
        )


__all__ = ["Stage1Workflow"]
