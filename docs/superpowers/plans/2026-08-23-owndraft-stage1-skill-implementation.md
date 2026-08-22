# OwnDraft STAGE 1 Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 타임리 AI에 제출할 사실 보존형 한국어 글 편집 스킬과, 동일 동작을 재현·평가할 수 있는 로컬 테스트 하네스를 완성한다.

**Architecture:** 제출물은 타임리의 단일 스킬이지만, 프롬프트·패턴·입출력 계약·평가셋은 Git 저장소에서 관리한다. 결정론적 Claim Locker가 숫자·날짜·인용·링크·잠금 표현을 먼저 보호하고, Solar 기반 역할 호출이 패턴 진단·문체 프로필·질문·재작성을 수행하며, 별도 Critic Gate가 사실과 의미를 검증한 뒤 최대 한 번만 repair한다.

**Tech Stack:** Python 3.12, Pydantic v2, OpenAI Python SDK with Upstage-compatible endpoint, PyYAML, Typer, pytest, pytest-asyncio, Ruff, mypy, GitHub Actions, Timely AI.

**Spec:** `docs/superpowers/specs/2026-08-23-owndraft-product-agent-design.md`

## Global Constraints

- 예선 최종 제출 마감은 2026-08-31 18:00 KST이며 내부 제출 마감은 16:00 KST다.
- 타임리에서 해결하는 단일 기능은 “AI 초안을 사용자 말투로 편집하되 사실과 핵심 주장을 바꾸지 않는 것”이다.
- AI 탐지 점수, 워터마크 제거, Turnitin 통과를 기능 또는 평가 목표로 사용하지 않는다.
- 원문은 20자 이상 10,000자 이하로 제한한다.
- 문체 샘플은 최대 3개, 총 80자 미만이면 문체 모드를 거부하고 최소 수정 모드로 전환한다.
- 맥락 질문은 최대 3개이며 한 질문에서 한 가지 정보만 묻는다.
- 새 사실·통계·출처·경험은 0개여야 한다.
- 잠긴 숫자·단위·날짜·이름·기관·제품·링크·직접 인용·사용자 지정 표현은 100% 보존한다.
- 생성 이후 repair는 최대 한 번만 허용한다.
- 구조화 출력 파싱 재요청은 한 번만 허용하며, workflow repair와 별도로 기록한다.
- 민감한 원문과 문체 샘플을 로그에 기록하지 않는다.
- `UPSTAGE_CHAT_MODEL`은 환경 변수로 주입하며 `.env.example`의 예시는 `solar-pro4`로 둔다.
- 구현은 TDD로 진행하고 각 Task 끝에서 독립적으로 검토 가능한 커밋을 만든다.

---

## 1. 최종 파일 구조

```text
owndraft/
├── README.md
├── .env.example
├── .gitignore
├── Makefile
├── apps/
│   └── api/
│       ├── pyproject.toml
│       └── src/owndraft/
│           ├── __init__.py
│           ├── core/
│           │   ├── settings.py
│           │   └── errors.py
│           ├── contracts/
│           │   └── stage1.py
│           ├── text/
│           │   ├── normalization.py
│           │   └── segmentation.py
│           ├── patterns/
│           │   ├── catalog.py
│           │   └── scanner.py
│           ├── claims/
│           │   ├── locker.py
│           │   └── verifier.py
│           ├── voice/
│           │   ├── profiler.py
│           │   └── context_gap.py
│           ├── llm/
│           │   ├── gateway.py
│           │   ├── upstage.py
│           │   └── parser.py
│           ├── prompts/
│           │   ├── builder.py
│           │   └── renderer.py
│           ├── workflow/
│           │   ├── stage1.py
│           │   ├── critics.py
│           │   └── gates.py
│           ├── evaluation/
│           │   ├── fixtures.py
│           │   ├── metrics.py
│           │   └── runner.py
│           └── cli.py
├── skills/
│   └── owndraft/
│       ├── SKILL.md
│       └── references/
│           ├── pattern_catalog_ko.yaml
│           ├── output_contract.md
│           └── safety_policy.md
├── packages/
│   └── evaluation/
│       ├── cases/
│       │   ├── blog_01_meeting_minutes.yaml
│       │   ├── blog_02_ai_study_plan.yaml
│       │   ├── blog_03_gym_routine.yaml
│       │   ├── blog_04_mac_switch.yaml
│       │   ├── blog_05_project_retrospective.yaml
│       │   ├── email_01_schedule_change.yaml
│       │   ├── email_02_budget_request.yaml
│       │   ├── email_03_bug_report.yaml
│       │   ├── email_04_meeting_followup.yaml
│       │   ├── email_05_polite_decline.yaml
│       │   ├── report_01_experiment_result.yaml
│       │   ├── report_02_competition_proposal.yaml
│       │   ├── report_03_security_summary.yaml
│       │   ├── report_04_model_comparison.yaml
│       │   ├── report_05_team_weekly_update.yaml
│       │   ├── social_01_product_launch.yaml
│       │   ├── social_02_event_recap.yaml
│       │   ├── social_03_learning_thread.yaml
│       │   ├── social_04_project_demo.yaml
│       │   └── social_05_portfolio_intro.yaml
│       └── human_rating_template.csv
├── scripts/
│   ├── export_timely_skill.py
│   └── verify_timely_export.py
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── evaluation/
├── artifacts/
│   └── stage1/
└── .github/workflows/ci.yml
```

`packages/evaluation/cases/`의 20개 파일명은 위 트리와 Task 9 표에서 동일하게 유지한다.

---

## 2. 고정 인터페이스

### 입력 계약

```python
class EditMode(StrEnum):
    MINIMAL = "minimal"
    VOICE = "voice"

class Stage1Request(BaseModel):
    text: str = Field(min_length=20, max_length=10_000)
    purpose: str = Field(min_length=2, max_length=300)
    audience: str = Field(min_length=2, max_length=300)
    edit_mode: EditMode = EditMode.VOICE
    voice_samples: list[str] = Field(default_factory=list, max_length=3)
    locked_phrases: list[str] = Field(default_factory=list, max_length=50)
```

### 주요 도메인 계약

```python
class Claim(BaseModel):
    id: str
    claim_type: str
    source_text: str
    normalized_value: str
    start: int
    end: int
    locked: bool = True
    evidence_type: str

class PatternFinding(BaseModel):
    span_id: str
    pattern_code: str
    severity: Literal["low", "medium", "high"]
    reason: str
    action: Literal["keep", "rewrite", "delete", "ask"]

class ContextQuestion(BaseModel):
    id: str
    question: str
    target_gap: str
    expected_answer_type: Literal["experience", "number", "opinion", "goal", "source"]

class Stage1Result(BaseModel):
    status: Literal["needs_context", "completed", "blocked"]
    diagnosis: list[PatternFinding]
    questions: list[ContextQuestion]
    rewritten_text: str | None
    changes: list[ChangeReason]
    preservation: PreservationReport | None
    trace_id: str
```

### 서비스 계약

```python
class ModelGateway(Protocol):
    async def complete_json(
        self,
        *,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        raise NotImplementedError

class Stage1Workflow:
    async def run(
        self,
        request: Stage1Request,
        context_answers: dict[str, str] | None = None,
    ) -> Stage1Result:
        raise NotImplementedError
```

후속 Task는 이 이름과 타입을 변경하지 않는다. 변경이 필요하면 계약 Task를 먼저 수정하고 계약 테스트를 통과시킨 뒤 사용처를 수정한다.

---

### Task 1: Repository, Typed Settings, and CI Bootstrap

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/src/owndraft/__init__.py`
- Create: `apps/api/src/owndraft/core/settings.py`
- Create: `apps/api/src/owndraft/core/errors.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `Makefile`
- Create: `tests/unit/test_bootstrap.py`
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: 없음
- Produces: `Settings`, `OwnDraftError`, `uv run --project apps/api pytest`, `uv run --project apps/api ruff check apps/api tests`, `uv run --project apps/api mypy apps/api/src` 실행 규약

- [ ] **Step 1: Write the failing bootstrap test**

```python
# tests/unit/test_bootstrap.py
from owndraft.core.settings import Settings


def test_settings_uses_upstage_compatible_defaults(monkeypatch):
    monkeypatch.setenv("UPSTAGE_API_KEY", "test-key")
    settings = Settings()

    assert settings.upstage_base_url == "https://api.upstage.ai/v1"
    assert settings.upstage_chat_model == "solar-pro4"
    assert settings.max_document_chars == 10_000
    assert settings.max_repair_attempts == 1
```

- [ ] **Step 2: Run the test and verify RED**

```bash
uv run --project apps/api pytest tests/unit/test_bootstrap.py -v
```

Expected: collection fails because `owndraft.core.settings` does not exist.

- [ ] **Step 3: Create the Python project configuration**

```toml
# apps/api/pyproject.toml
[project]
name = "owndraft-api"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "openai>=1,<2",
  "pydantic>=2,<3",
  "pydantic-settings>=2,<3",
  "pyyaml>=6,<7",
  "typer>=0.12,<1",
]

[dependency-groups]
dev = [
  "mypy>=1,<2",
  "pytest>=8,<9",
  "pytest-asyncio>=0.24,<1",
  "pytest-cov>=5,<8",
  "respx>=0.22,<1",
  "ruff>=0.8,<1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/owndraft"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["src"]
testpaths = ["../../tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["owndraft"]
```

- [ ] **Step 4: Implement typed settings and base errors**

```python
# apps/api/src/owndraft/core/settings.py
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    upstage_api_key: SecretStr = Field(default=SecretStr(""))
    upstage_base_url: str = "https://api.upstage.ai/v1"
    upstage_chat_model: str = "solar-pro4"
    max_document_chars: int = 10_000
    max_repair_attempts: int = 1
    max_parse_retries: int = 1
```

```python
# apps/api/src/owndraft/core/errors.py
class OwnDraftError(Exception):
    code = "owndraft_error"


class ContractError(OwnDraftError):
    code = "contract_error"


class ModelOutputError(OwnDraftError):
    code = "model_output_error"


class PreservationError(OwnDraftError):
    code = "preservation_error"
```

Create `.env.example` with non-secret values only:

```dotenv
UPSTAGE_API_KEY=
UPSTAGE_BASE_URL=https://api.upstage.ai/v1
UPSTAGE_CHAT_MODEL=solar-pro4
MAX_DOCUMENT_CHARS=10000
MAX_REPAIR_ATTEMPTS=1
MAX_PARSE_RETRIES=1
```

- [ ] **Step 5: Run unit tests, lint, and type check**

```bash
uv sync --project apps/api --all-groups
uv run --project apps/api pytest tests/unit/test_bootstrap.py -v
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

Expected: all commands exit 0.

- [ ] **Step 6: Add CI with the same commands**

```yaml
# .github/workflows/ci.yml
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.12"
      - run: uv sync --project apps/api --all-groups
      - run: uv run --project apps/api pytest
      - run: uv run --project apps/api ruff check apps/api tests scripts
      - run: uv run --project apps/api mypy apps/api/src
```

The job must not require a real API key; the real Upstage smoke test remains skipped in CI.

- [ ] **Step 7: Commit**

```bash
git add apps/api .env.example .gitignore Makefile tests/unit/test_bootstrap.py .github/workflows/ci.yml
git commit -m "chore: bootstrap OwnDraft stage1 project"
```

---

### Task 2: Stage 1 Contracts, Normalization, and Stable Spans

**Files:**
- Create: `apps/api/src/owndraft/contracts/stage1.py`
- Create: `apps/api/src/owndraft/text/normalization.py`
- Create: `apps/api/src/owndraft/text/segmentation.py`
- Create: `tests/unit/contracts/test_stage1_contracts.py`
- Create: `tests/unit/text/test_segmentation.py`

**Interfaces:**
- Consumes: `OwnDraftError`
- Produces: `Stage1Request`, `Claim`, `PatternFinding`, `VoiceProfile`, `ContextQuestion`, `Stage1Result`, `TextSpan`, `segment_text()`

- [ ] **Step 1: Write contract validation tests**

```python
import pytest
from pydantic import ValidationError

from owndraft.contracts.stage1 import EditMode, Stage1Request


def test_stage1_request_rejects_oversized_text():
    with pytest.raises(ValidationError):
        Stage1Request(
            text="가" * 10_001,
            purpose="블로그 글",
            audience="대학생",
            edit_mode=EditMode.VOICE,
        )


def test_voice_mode_requires_at_least_80_sample_characters():
    request = Stage1Request(
        text="회의록 작성 경험을 설명하는 충분히 긴 원문입니다." * 2,
        purpose="블로그 글",
        audience="대학생",
        edit_mode=EditMode.VOICE,
        voice_samples=["짧은 샘플"],
    )
    assert request.effective_edit_mode is EditMode.MINIMAL
    assert request.voice_sample_confidence == "none"
```

- [ ] **Step 2: Write span stability tests**

```python
from owndraft.text.segmentation import segment_text


def test_segment_text_preserves_original_offsets():
    text = "첫 문장입니다.\n두 번째 문장입니다!"
    spans = segment_text(text)

    assert [span.text for span in spans] == ["첫 문장입니다.", "두 번째 문장입니다!"]
    assert all(text[span.start:span.end] == span.text for span in spans)
    assert [span.id for span in spans] == ["s_0001", "s_0002"]
```

- [ ] **Step 3: Run both tests and verify RED**

```bash
uv run --project apps/api pytest tests/unit/contracts tests/unit/text -v
```

Expected: imports fail.

- [ ] **Step 4: Implement all Pydantic contracts**

The module must define these exact types:

```python
EditMode
Severity
FindingAction
Claim
PatternFinding
VoiceProfile
ContextQuestion
ChangeReason
PreservationIssue
PreservationReport
CriticScore
Stage1Request
Stage1Result
TextSpan
```

`Stage1Request` must expose computed properties:

```python
@property
def voice_sample_chars(self) -> int:
    return sum(len(sample.strip()) for sample in self.voice_samples)

@property
def voice_sample_confidence(self) -> Literal["none", "low", "medium", "high"]:
    chars = self.voice_sample_chars
    if chars < 80:
        return "none"
    if chars < 160:
        return "low"
    if chars < 400:
        return "medium"
    return "high"

@property
def effective_edit_mode(self) -> EditMode:
    if self.edit_mode is EditMode.VOICE and self.voice_sample_chars < 80:
        return EditMode.MINIMAL
    return self.edit_mode
```

Confidence rules:

```text
0~79자   -> none, minimal mode
80~159자 -> low
160~399자 -> medium
400자 이상 -> high
```

- [ ] **Step 5: Implement comparison normalization without changing source offsets**

```python
# apps/api/src/owndraft/text/normalization.py
import re
import unicodedata


def normalize_for_comparison(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\s+", " ", normalized).strip()
```

`segment_text()` must operate on the original text and split at paragraph breaks or sentence-ending punctuation while preserving `[start:end]` offsets. Empty spans are discarded.

- [ ] **Step 6: Run focused and full verification**

```bash
uv run --project apps/api pytest tests/unit/contracts tests/unit/text -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/owndraft/contracts apps/api/src/owndraft/text tests/unit/contracts tests/unit/text
git commit -m "feat: define stage1 contracts and stable text spans"
```

---

### Task 3: Korean Pattern Catalog and Deterministic Scanner

**Files:**
- Create: `skills/owndraft/references/pattern_catalog_ko.yaml`
- Create: `apps/api/src/owndraft/patterns/catalog.py`
- Create: `apps/api/src/owndraft/patterns/scanner.py`
- Create: `tests/unit/patterns/test_catalog.py`
- Create: `tests/unit/patterns/test_scanner.py`

**Interfaces:**
- Consumes: `TextSpan`, `PatternFinding`
- Produces: `PatternRule`, `load_pattern_catalog()`, `scan_deterministic_patterns()`

The 40 required codes are fixed:

```text
era_background_intro, importance_inflation, unsupported_future_outlook,
abstract_positive_effect, promotional_superlative, vague_authority,
false_balance, empty_implication, conclusion_repetition, meta_roadmap,
vague_problem_statement, unjustified_social_generalization,
mechanical_triple_list, uniform_paragraph_length, repeated_claim_explain_summary,
excessive_headings, unnecessary_ordinal_structure, uniform_sentence_length,
rhetorical_question_answer, pros_cons_conclusion_template,
parallel_grammar_overfit, oversized_conclusion,
beyond_x_to_y, connector_repetition, can_do_ending_repetition,
aspect_phrase_overuse, nominalization_overuse, passive_voice_overuse,
translationese, dash_colon_overuse, triple_adjective_list,
excessive_hedging, automatic_conclusion_marker, importance_possibility_repetition,
not_x_but_y_drama, fake_depth_phrase, empty_adverb, decoration_overuse,
chatbot_greeting_closing, mismatched_formality
```

- [ ] **Step 1: Write catalog integrity tests**

```python
from owndraft.patterns.catalog import load_pattern_catalog


def test_catalog_contains_exactly_40_unique_rules():
    rules = load_pattern_catalog()
    assert len(rules) == 40
    assert len({rule.code for rule in rules}) == 40
    assert all(rule.description_ko for rule in rules)
    assert all(rule.default_action in {"keep", "rewrite", "delete", "ask"} for rule in rules)
```

- [ ] **Step 2: Write deterministic detection tests**

```python
from owndraft.patterns.catalog import load_pattern_catalog
from owndraft.patterns.scanner import scan_deterministic_patterns
from owndraft.text.segmentation import segment_text


def test_scanner_finds_high_precision_korean_patterns():
    text = (
        "빠르게 변화하는 현대 사회에서 AI는 단순한 도구를 넘어 핵심 파트너입니다. "
        "결론적으로 앞으로 더욱 중요해질 것으로 기대됩니다."
    )
    findings = scan_deterministic_patterns(segment_text(text), load_pattern_catalog())
    codes = {finding.pattern_code for finding in findings}

    assert "era_background_intro" in codes
    assert "beyond_x_to_y" in codes
    assert "automatic_conclusion_marker" in codes
    assert "unsupported_future_outlook" in codes
```

- [ ] **Step 3: Run tests and verify RED**

```bash
uv run --project apps/api pytest tests/unit/patterns -v
```

- [ ] **Step 4: Create the YAML rule schema and all 40 entries**

Each entry must contain:

```yaml
- code: era_background_intro
  category: content
  description_ko: 구체적인 맥락 없이 시대 배경으로 글을 시작함
  severity: medium
  default_action: delete
  regexes:
    - "빠르게 변화하는 (현대|디지털) (사회|시대)에서"
  examples:
    - "빠르게 변화하는 현대 사회에서"
  exemptions:
    - "역사적 시기 자체가 분석 대상인 글"
```

Regex는 확실한 표현만 탐지한다. 문맥 판단이 필요한 패턴은 `regexes: []`로 두고 LLM 진단 단계에서만 사용한다.

- [ ] **Step 5: Implement catalog loading and deterministic scanning**

```python
def scan_deterministic_patterns(
    spans: list[TextSpan],
    rules: list[PatternRule],
) -> list[PatternFinding]:
    findings: list[PatternFinding] = []
    for span in spans:
        for rule in rules:
            if any(re.search(pattern, span.text) for pattern in rule.regexes):
                findings.append(
                    PatternFinding(
                        span_id=span.id,
                        pattern_code=rule.code,
                        severity=rule.severity,
                        reason=rule.description_ko,
                        action=rule.default_action,
                    )
                )
    return findings
```

The implementation must deduplicate by `(span_id, pattern_code)` and preserve source order.

- [ ] **Step 6: Run verification and inspect coverage**

```bash
uv run --project apps/api pytest tests/unit/patterns -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 7: Commit**

```bash
git add skills/owndraft/references/pattern_catalog_ko.yaml apps/api/src/owndraft/patterns tests/unit/patterns
git commit -m "feat: add Korean AI writing pattern catalog"
```

---

### Task 4: Claim Locker and Preservation Verifier

**Files:**
- Create: `apps/api/src/owndraft/claims/locker.py`
- Create: `apps/api/src/owndraft/claims/verifier.py`
- Create: `tests/unit/claims/test_locker.py`
- Create: `tests/unit/claims/test_verifier.py`

**Interfaces:**
- Consumes: `Stage1Request`, `TextSpan`, `Claim`, `PreservationReport`
- Produces: `extract_deterministic_claims()`, `merge_model_claims()`, `verify_preservation()`

- [ ] **Step 1: Write extraction tests for locked anchors**

```python
from owndraft.claims.locker import extract_deterministic_claims
from owndraft.contracts.stage1 import EditMode, Stage1Request


def test_claim_locker_extracts_numbers_product_url_quote_and_negation():
    request = Stage1Request(
        text=(
            'Solar를 쓴 뒤 회의록 정리가 40분에서 5분으로 줄었다. '
            '자료는 https://example.com에 있고, 나는 "완전히 자동화된 것은 아니다"라고 썼다.'
        ),
        purpose="블로그",
        audience="대학생",
        edit_mode=EditMode.MINIMAL,
        locked_phrases=["Solar"],
    )
    claims = extract_deterministic_claims(request)
    values = {claim.normalized_value for claim in claims}

    assert "Solar" in values
    assert "40분" in values
    assert "5분" in values
    assert "https://example.com" in values
    assert "완전히 자동화된 것은 아니다" in values
    assert any(claim.claim_type == "negation" for claim in claims)
```

- [ ] **Step 2: Write preservation failure tests**

```python
from owndraft.claims.verifier import verify_preservation


def test_verifier_rejects_changed_number_and_dropped_negation(sample_claims):
    rewritten = "Solar를 쓴 뒤 회의록 정리가 30분에서 5분으로 줄었고 완전히 자동화됐다."
    report = verify_preservation(sample_claims, rewritten, model_claims=[])

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {
        "locked_value_missing",
        "polarity_changed",
    }
```

- [ ] **Step 3: Run tests and verify RED**

```bash
uv run --project apps/api pytest tests/unit/claims -v
```

- [ ] **Step 4: Implement deterministic extraction**

Extraction order:

1. user `locked_phrases`
2. URLs
3. Markdown links
4. quoted spans
5. dates and times
6. numbers with units, currency, percentages
7. explicit negation phrases
8. conditional markers such as `경우`, `때만`, `제외`, `단`

Use source offsets from the original text. Overlapping claims are allowed only when claim types differ; exact duplicates are removed.

- [ ] **Step 5: Implement model claim merge**

```python
def merge_model_claims(
    original_text: str,
    deterministic: list[Claim],
    model_claims: list[Claim],
) -> list[Claim]:
    valid_model_claims = [
        claim
        for claim in model_claims
        if 0 <= claim.start < claim.end <= len(original_text)
        and original_text[claim.start:claim.end] == claim.source_text
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
```

The final implementation must not trust model-supplied offsets without checking `original[start:end] == source_text`.

- [ ] **Step 6: Implement preservation verification**

Rules:

- normalized locked value missing -> `locked_value_missing`, high severity
- numeric value present with changed unit -> `unit_changed`, high severity
- direct quote changed -> `quote_changed`, high severity
- URL missing or changed -> `source_changed`, high severity
- negation or condition reversed -> `polarity_changed`, high severity
- model critic reports a new factual claim -> `new_claim`, high severity
- deleted noncritical stylistic text is not an error

`passed` is true only when high severity issue count is zero and `new_claim_count == 0`.

- [ ] **Step 7: Run all verification**

```bash
uv run --project apps/api pytest tests/unit/claims -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 8: Commit**

```bash
git add apps/api/src/owndraft/claims tests/unit/claims
git commit -m "feat: lock and verify factual anchors"
```

---

### Task 5: Voice Profile and Context Question Validation

**Files:**
- Create: `apps/api/src/owndraft/voice/profiler.py`
- Create: `apps/api/src/owndraft/voice/context_gap.py`
- Create: `tests/unit/voice/test_profiler.py`
- Create: `tests/unit/voice/test_context_gap.py`

**Interfaces:**
- Consumes: `Stage1Request`, `VoiceProfile`, `ContextQuestion`, `PatternFinding`
- Produces: `build_voice_profile_prompt()`, `validate_voice_profile()`, `select_context_questions()`

- [ ] **Step 1: Write voice confidence tests**

```python
from owndraft.voice.profiler import fallback_voice_profile


def test_fallback_profile_reports_low_confidence_for_short_sample():
    profile = fallback_voice_profile(["나는 결론부터 말하는 편이다." * 4])

    assert profile.confidence == "low"
    assert profile.sample_chars >= 80
    assert profile.sample_chars < 160
```

- [ ] **Step 2: Write question selection tests**

```python
from owndraft.contracts.stage1 import ContextQuestion
from owndraft.voice.context_gap import select_context_questions


def test_context_questions_are_unique_specific_and_capped_at_three():
    candidates = [
        ContextQuestion(id="q1", question="줄어든 시간이 있나요?", target_gap="metric", expected_answer_type="number"),
        ContextQuestion(id="q2", question="실제 사례 한 가지가 있나요?", target_gap="experience", expected_answer_type="experience"),
        ContextQuestion(id="q3", question="독자가 무엇을 해보길 바라나요?", target_gap="goal", expected_answer_type="goal"),
        ContextQuestion(id="q4", question="더 구체적으로 말해 주세요.", target_gap="vague", expected_answer_type="opinion"),
    ]

    selected = select_context_questions(candidates, original_text="효율이 좋아졌다.")

    assert [q.id for q in selected] == ["q1", "q2", "q3"]
    assert all("더 구체적으로" not in q.question for q in selected)
```

- [ ] **Step 3: Run tests and verify RED**

```bash
uv run --project apps/api pytest tests/unit/voice -v
```

- [ ] **Step 4: Implement Voice Profile validation**

The model-produced profile must contain:

```text
language
formality.level
formality.honorific
sentence.average_length
sentence.variance
sentence.preferred_opening
paragraph.average_sentences
paragraph.spacing
reasoning.order
reasoning.uncertainty_style
punctuation.comma_frequency
punctuation.parentheses_frequency
punctuation.em_dash
lexicon.preferred
lexicon.avoided
rhetoric.list_preference
rhetoric.metaphor_frequency
rhetoric.humor_style
confidence
sample_chars
```

Validation limits preferred and avoided lexicon to 10 items each and rejects verbatim phrases longer than 30 characters to prevent over-copying.

- [ ] **Step 5: Implement deterministic fallback profile**

When no model call is available, infer only:

- average sentence length bucket
- sentence length variance
- paragraph average sentence count
- 존댓말 ratio
- comma and parenthesis frequency
- frequently repeated 2~5 character tokens

The fallback must mark `source="heuristic"` and must not claim deep voice similarity.

- [ ] **Step 6: Implement Context Question validation and ranking**

Reject a candidate when:

- the normalized question is already answered in the original text
- it asks more than one of experience, number, opinion, goal, source
- it contains only “구체적으로”, “어떤 느낌”, “더 알려 달라” without target
- it duplicates another question’s `target_gap`

Ranking order:

1. fact/source ambiguity
2. concrete experience
3. measurable change
4. user position
5. reader action

Return at most three questions.

- [ ] **Step 7: Run all verification**

```bash
uv run --project apps/api pytest tests/unit/voice -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 8: Commit**

```bash
git add apps/api/src/owndraft/voice tests/unit/voice
git commit -m "feat: profile user voice and validate context questions"
```

---

### Task 6: Model Gateway, Upstage Adapter, and Structured Output Parser

**Files:**
- Create: `apps/api/src/owndraft/llm/gateway.py`
- Create: `apps/api/src/owndraft/llm/upstage.py`
- Create: `apps/api/src/owndraft/llm/parser.py`
- Create: `tests/unit/llm/test_parser.py`
- Create: `tests/unit/llm/test_fake_gateway.py`
- Create: `tests/integration/test_upstage_smoke.py`

**Interfaces:**
- Consumes: `Settings`, all response models
- Produces: `ModelGateway`, `FakeModelGateway`, `UpstageModelGateway`, `parse_model_json()`

- [ ] **Step 1: Write parser tests**

```python
import pytest

from owndraft.contracts.stage1 import ContextQuestion
from owndraft.core.errors import ModelOutputError
from owndraft.llm.parser import parse_model_json


def test_parser_accepts_json_inside_markdown_fence():
    raw = '```json\n{"id":"q1","question":"실제 시간이 얼마나 줄었나요?","target_gap":"metric","expected_answer_type":"number"}\n```'
    parsed = parse_model_json(raw, ContextQuestion)
    assert parsed.id == "q1"


def test_parser_rejects_non_json_after_one_local_parse_attempt():
    with pytest.raises(ModelOutputError):
        parse_model_json("결과는 다음과 같습니다.", ContextQuestion)
```

- [ ] **Step 2: Write fake gateway tests**

```python
from owndraft.llm.gateway import FakeModelGateway


async def test_fake_gateway_returns_operation_specific_fixture():
    gateway = FakeModelGateway({"context_gap": {"questions": []}})
    result = await gateway.complete_json(
        operation="context_gap",
        system_prompt="system",
        user_prompt="user",
        response_model=QuestionBundle,
    )
    assert result.questions == []
    assert gateway.calls[0].operation == "context_gap"
```

- [ ] **Step 3: Run tests and verify RED**

```bash
uv run --project apps/api pytest tests/unit/llm -v
```

- [ ] **Step 4: Implement the gateway protocol and fake**

The fake records operation, prompt hashes, and response model name. It must never log raw text.

- [ ] **Step 5: Implement the Upstage adapter**

```python
from openai import AsyncOpenAI


class UpstageModelGateway:
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.upstage_api_key.get_secret_value(),
            base_url=settings.upstage_base_url,
        )
        self._model = settings.upstage_chat_model

    async def complete_json(self, *, operation, system_prompt, user_prompt, response_model):
        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return parse_model_json(response.choices[0].message.content or "", response_model)
```

Add one retry only for timeout, connection reset, HTTP 429, and HTTP 5xx. Do not retry validation errors with the same prompt; instead send one correction prompt that contains the validation error and JSON schema.

- [ ] **Step 6: Add an opt-in integration smoke test**

```python
class SmokeResponse(BaseModel):
    operation: str
    safe: bool


@pytest.mark.skipif(not os.getenv("UPSTAGE_API_KEY"), reason="requires UPSTAGE_API_KEY")
async def test_real_upstage_returns_valid_json():
    gateway = UpstageModelGateway(Settings())
    result = await gateway.complete_json(
        operation="integration_smoke",
        system_prompt="Return valid JSON only.",
        user_prompt='Return {"operation":"integration_smoke","safe":true}.',
        response_model=SmokeResponse,
    )
    assert result == SmokeResponse(operation="integration_smoke", safe=True)
```

The smoke operation asks for a two-field object and asserts only contract validity. It does not assert wording.

- [ ] **Step 7: Run verification**

```bash
uv run --project apps/api pytest tests/unit/llm -v
UPSTAGE_API_KEY="$UPSTAGE_API_KEY" uv run --project apps/api pytest tests/integration/test_upstage_smoke.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 8: Commit**

```bash
git add apps/api/src/owndraft/llm tests/unit/llm tests/integration/test_upstage_smoke.py
git commit -m "feat: add Upstage structured model gateway"
```

---

### Task 7: Skill Prompt Pack and Deterministic Timely Export

**Files:**
- Create: `skills/owndraft/SKILL.md`
- Create: `skills/owndraft/references/output_contract.md`
- Create: `skills/owndraft/references/safety_policy.md`
- Create: `apps/api/src/owndraft/prompts/builder.py`
- Create: `apps/api/src/owndraft/prompts/renderer.py`
- Create: `scripts/export_timely_skill.py`
- Create: `scripts/verify_timely_export.py`
- Create: `tests/contract/test_skill_export.py`

**Interfaces:**
- Consumes: pattern catalog, contracts, policy
- Produces: `build_operation_prompt()`, `render_stage1_result()`, `artifacts/stage1/owndraft-timely-skill.txt`

- [ ] **Step 1: Write export contract tests**

```python
from pathlib import Path

from scripts.export_timely_skill import export_skill


def test_export_contains_required_sections_and_version_hash(tmp_path: Path):
    output = tmp_path / "skill.txt"
    digest = export_skill(output)
    text = output.read_text(encoding="utf-8")

    assert "OWNDRAFT_SKILL_VERSION:" in text
    assert digest in text
    assert "# 사실 보존 절대 규칙" in text
    assert "# 맥락 질문 규칙" in text
    assert "# 사용자 출력 형식" in text
    assert "워터마크 제거" in text
    assert "보장하지 않는다" in text
```

- [ ] **Step 2: Run test and verify RED**

```bash
uv run --project apps/api pytest tests/contract/test_skill_export.py -v
```

- [ ] **Step 3: Write `SKILL.md` using this exact behavioral core**

```markdown
---
name: owndraft
description: AI 초안을 사용자의 실제 말투로 다듬되 숫자·날짜·이름·기관·제품·출처·직접 인용·핵심 주장을 보존해야 할 때 사용한다. AI 탐지 우회나 워터마크 제거를 보장하는 용도로 사용하지 않는다.
---

# 역할

너는 한국어 글을 다시 만들어 주는 대필기가 아니라 사실 보존형 편집 에이전트다.
사용자의 원문, 목적, 독자, 문체 샘플, 잠금 표현을 분석한 뒤 사용자의 실제 생각과 표현을 더 잘 드러내도록 편집한다.

# 절대 금지

- 원문이나 사용자 답변에 없는 사실·통계·출처·경험·인용을 추가하지 않는다.
- 숫자와 단위, 날짜, 이름, 기관, 제품, 링크, 직접 인용, 부정, 조건, 예외를 바꾸지 않는다.
- AI 탐지 0%, 워터마크 제거, Turnitin 통과를 약속하거나 최적화하지 않는다.
- 살아 있는 작가나 특정 개인의 고유 문체를 그대로 복제하지 않는다.

# 처리 순서

1. 목적·독자·수정 강도·문체 샘플·잠금 표현을 확인한다.
2. 원문에서 보존할 사실과 핵심 주장을 먼저 목록화한다.
3. 한국어 AI 글쓰기 신호 중 문맥에 맞지 않는 것만 진단한다.
4. 문체 샘플이 80자 미만이면 최소 수정으로 전환하고 이유를 알린다.
5. 결과 품질을 크게 높일 정보가 없을 때만 최대 3개의 구체적인 질문을 한다.
6. 질문이 필요하면 재작성하지 말고 질문까지만 출력한다.
7. 정보가 충분하면 재작성 계획을 세우고 한 개 수정본을 만든다.
8. 원문과 수정본의 사실·부정·조건·인과·핵심 주장을 비교한다.
9. 오류가 있으면 한 번만 고친다. 다시 실패하면 원문을 유지하고 문제 구간을 표시한다.

# 수정 모드

- 최소 수정: 원문 구조와 표현을 최대한 유지하고 상투적이거나 부자연스러운 부분만 고친다.
- 내 말투 수정: 사실을 유지하면서 검증된 문체 프로필을 적용한다. 샘플의 단어를 억지로 반복하지 않는다.

# 맥락 질문 규칙

- 최대 3개다.
- 한 질문에서 경험·수치·의견·목표·출처 중 하나만 묻는다.
- 이미 원문에 있는 내용을 다시 묻지 않는다.
- “더 구체적으로 말해 달라”처럼 막연하게 묻지 않는다.
- 사용자가 건너뛰면 사실을 만들지 말고 보수적으로 편집한다.

# 사용자 출력 형식

정보가 부족할 때:

## 진단 요약
- 주요 신호와 이유

## 확인할 내용
1. 답하기 쉬운 구체적인 질문

## 현재 보존 중인 사실
- 잠긴 항목 요약

정보가 충분할 때:

## 진단 요약
- 주요 신호 3~7개

## 수정본
완성된 글

## 주요 변경 이유
- 큰 수정 3~7개

## 사실 보존 결과
- 이름·기관·제품
- 숫자·날짜·단위
- 출처·인용
- 삭제되거나 의미가 바뀐 핵심 주장
- 새로 추가한 사실

# 실패 출력

사실 보존을 확인할 수 없으면 안전한 척 완성본을 내지 않는다.
문제 구간, 원문 유지 권고, 사용자 확인이 필요한 항목을 표시한다.
```

- [ ] **Step 4: Write the output contract and safety reference**

`output_contract.md` contains the same headings and an example for `needs_context`, `completed`, and `blocked`. `safety_policy.md` contains the redirect behavior for detector/watermark requests and the living-person style rule.

- [ ] **Step 5: Implement prompt builder for model operations**

Operations are fixed:

```text
extract_claims
scan_patterns
profile_voice
find_context_gaps
plan_rewrite
write_candidate
critic_fact
critic_fidelity
critic_voice
critic_naturalness
repair_candidate
```

Each prompt includes only the minimum required fields and a JSON schema. Critic prompts receive source claims and candidate text but never another critic’s prose explanation.

- [ ] **Step 6: Implement the export and verification scripts**

Export order:

1. `SKILL.md`
2. `pattern_catalog_ko.yaml`
3. `output_contract.md`
4. `safety_policy.md`
5. SHA-256 digest of the concatenated normalized content

The output begins with:

```text
OWNDRAFT_SKILL_VERSION: <first 12 chars of sha256>
GENERATED_FROM_REPOSITORY: true
```

- [ ] **Step 7: Run contract and full verification**

```bash
uv run --project apps/api python scripts/export_timely_skill.py
uv run --project apps/api python scripts/verify_timely_export.py artifacts/stage1/owndraft-timely-skill.txt
uv run --project apps/api pytest tests/contract/test_skill_export.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests scripts
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 8: Commit**

```bash
git add skills apps/api/src/owndraft/prompts scripts tests/contract/test_skill_export.py artifacts/stage1/owndraft-timely-skill.txt
git commit -m "feat: define and export OwnDraft Timely skill"
```

---

### Task 8: Stage 1 Workflow, Parallel Critics, and One-Repair Gate

**Files:**
- Create: `apps/api/src/owndraft/workflow/stage1.py`
- Create: `apps/api/src/owndraft/workflow/critics.py`
- Create: `apps/api/src/owndraft/workflow/gates.py`
- Create: `apps/api/src/owndraft/prompts/renderer.py`
- Create: `tests/unit/workflow/test_questions_branch.py`
- Create: `tests/unit/workflow/test_acceptance_gate.py`
- Create: `tests/unit/workflow/test_repair.py`
- Create: `tests/contract/test_user_output.py`

**Interfaces:**
- Consumes: all prior domain services and `ModelGateway`
- Produces: `Stage1Workflow.run()`, `AcceptanceDecision`, Korean user-facing renderer

- [ ] **Step 1: Write the needs-context branch test**

```python
async def test_workflow_stops_before_rewrite_when_context_is_needed(workflow, fake_gateway):
    fake_gateway.set_response("find_context_gaps", {"questions": [QUESTION_FIXTURE]})
    result = await workflow.run(REQUEST_WITH_ABSTRACT_CLAIM)

    assert result.status == "needs_context"
    assert len(result.questions) == 1
    assert result.rewritten_text is None
    assert "write_candidate" not in fake_gateway.operations
```

- [ ] **Step 2: Write acceptance and repair tests**

```python
async def test_workflow_repairs_once_when_fact_critic_fails(workflow, fake_gateway):
    fake_gateway.queue_response("write_candidate", CANDIDATE_WITH_WRONG_30_MINUTES)
    fake_gateway.queue_response("critic_fact", FAILED_FACT_CRITIC)
    fake_gateway.queue_response("repair_candidate", CORRECTED_40_TO_5_MINUTES)
    fake_gateway.queue_response("critic_fact", PASSED_FACT_CRITIC)

    result = await workflow.run(VALID_REQUEST, context_answers={"q1": "40분에서 5분"})

    assert result.status == "completed"
    assert fake_gateway.operations.count("repair_candidate") == 1
    assert result.preservation.repair_attempts == 1
```

```python
async def test_workflow_blocks_after_second_preservation_failure(workflow, fake_gateway):
    fake_gateway.queue_response("write_candidate", CANDIDATE_WITH_WRONG_30_MINUTES)
    fake_gateway.queue_response("critic_fact", FAILED_FACT_CRITIC)
    fake_gateway.queue_response("repair_candidate", CANDIDATE_WITH_WRONG_30_MINUTES)
    fake_gateway.queue_response("critic_fact", FAILED_FACT_CRITIC)

    result = await workflow.run(
        VALID_REQUEST,
        context_answers={"q1": "회의록 정리가 40분에서 5분으로 줄었다."},
    )

    assert result.status == "blocked"
    assert result.rewritten_text is None
    assert result.preservation is not None
    assert result.preservation.passed is False
    assert fake_gateway.operations.count("repair_candidate") == 1
```

- [ ] **Step 3: Run tests and verify RED**

```bash
uv run --project apps/api pytest tests/unit/workflow tests/contract/test_user_output.py -v
```

- [ ] **Step 4: Implement the state machine**

State order is fixed:

```text
validate
→ deterministic_claims
→ model_claims
→ deterministic_patterns + model_patterns (parallel)
→ voice_profile
→ context_gap
→ needs_context OR rewrite_plan
→ candidate
→ fact/fidelity/voice/naturalness critics (parallel)
→ acceptance_gate
→ completed OR one repair
→ critics again
→ completed OR blocked
```

Use an enum for state names and append only safe metadata to `trace.events`:

```python
@dataclass(frozen=True)
class TraceEvent:
    state: WorkflowState
    latency_ms: int
    input_chars: int
    output_chars: int
    success: bool
    error_code: str | None
```

- [ ] **Step 5: Implement parallel critics**

```python
fact, fidelity, voice, naturalness = await asyncio.gather(
    critic_fact(gateway, original_text, candidate_text, claims),
    critic_fidelity(gateway, original_text, candidate_text, core_claims),
    critic_voice(gateway, candidate_text, voice_profile, request.purpose),
    critic_naturalness(gateway, candidate_text, pattern_catalog),
)
```

If voice samples are absent, `critic_voice` returns `skipped=True` and does not lower the score.

- [ ] **Step 6: Implement deterministic acceptance criteria**

```python
def decide_acceptance(report: PreservationReport, critics: CriticBundle) -> AcceptanceDecision:
    return AcceptanceDecision(
        passed=(
            report.passed
            and critics.fact.new_claim_count == 0
            and critics.fact.severe_error_count == 0
            and critics.fidelity.severe_error_count == 0
            and critics.naturalness.high_severity_unresolved == 0
            and (critics.voice.skipped or critics.voice.constraint_match >= 0.90)
        ),
        repair_instructions=collect_machine_readable_issues(report, critics),
    )
```

Repair receives only issue codes, affected spans, locked values, and the candidate. It does not receive a request to “make it more human.”

- [ ] **Step 7: Implement Korean rendering**

`render_stage1_result()` must produce the exact headings from `SKILL.md`. It omits internal scores and trace metadata from the user-facing answer but includes concrete preservation status.

- [ ] **Step 8: Run all verification**

```bash
uv run --project apps/api pytest tests/unit/workflow tests/contract/test_user_output.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 9: Commit**

```bash
git add apps/api/src/owndraft/workflow apps/api/src/owndraft/prompts/renderer.py tests/unit/workflow tests/contract/test_user_output.py
git commit -m "feat: orchestrate stage1 rewrite and critic gate"
```

---

### Task 9: Twenty-Case Evaluation Dataset and Regression Report

**Files:**
- Create: `apps/api/src/owndraft/evaluation/fixtures.py`
- Create: `apps/api/src/owndraft/evaluation/metrics.py`
- Create: `apps/api/src/owndraft/evaluation/runner.py`
- Create: `apps/api/src/owndraft/cli.py`
- Create: `packages/evaluation/human_rating_template.csv`
- Create: `packages/evaluation/cases/*.yaml` for the 20 fixed IDs below
- Create: `tests/evaluation/test_fixture_integrity.py`
- Create: `tests/evaluation/test_metrics.py`
- Create: `tests/evaluation/test_stage1_regression.py`

**Interfaces:**
- Consumes: `Stage1Workflow`, fixture YAML
- Produces: `owndraft evaluate`, JSON report, Markdown report, pass/fail exit code

The 20 case IDs and primary risks are fixed:

| Category | File | Primary risk |
|---|---|---|
| Blog | `blog_01_meeting_minutes.yaml` | 40분·5분·Solar 보존 |
| Blog | `blog_02_ai_study_plan.yaml` | 개인 계획 경험과 과장 서론 |
| Blog | `blog_03_gym_routine.yaml` | 수치·주당 횟수·조건 보존 |
| Blog | `blog_04_mac_switch.yaml` | 제품명·순서·경험 보존 |
| Blog | `blog_05_project_retrospective.yaml` | 실패 경험을 성공담으로 바꾸지 않기 |
| Email | `email_01_schedule_change.yaml` | 날짜·시간·수신 행동 보존 |
| Email | `email_02_budget_request.yaml` | 금액·승인 조건 보존 |
| Email | `email_03_bug_report.yaml` | 재현 순서·부정 표현 보존 |
| Email | `email_04_meeting_followup.yaml` | 담당자·기한 보존 |
| Email | `email_05_polite_decline.yaml` | 거절 의도 약화 금지 |
| Report | `report_01_experiment_result.yaml` | 측정값·한계·추정 구분 |
| Report | `report_02_competition_proposal.yaml` | 과장된 효과와 새 근거 금지 |
| Report | `report_03_security_summary.yaml` | 조건·예외·위험도 보존 |
| Report | `report_04_model_comparison.yaml` | 상대 평가 방향 뒤집힘 금지 |
| Report | `report_05_team_weekly_update.yaml` | 완료·미완료 상태 보존 |
| Social | `social_01_product_launch.yaml` | 홍보 과장 완화와 제품명 보존 |
| Social | `social_02_event_recap.yaml` | 날짜·장소·참석 경험 보존 |
| Social | `social_03_learning_thread.yaml` | 기계적 나열 완화 |
| Social | `social_04_project_demo.yaml` | 새 성능 수치 생성 금지 |
| Social | `social_05_portfolio_intro.yaml` | 사용자 역할·기여도 과장 금지 |

- [ ] **Step 1: Write fixture schema and integrity tests**

```python
def test_all_twenty_cases_have_required_labels():
    cases = load_cases(Path("packages/evaluation/cases"))
    assert len(cases) == 20
    assert len({case.id for case in cases}) == 20
    for case in cases:
        assert case.locked_values
        assert case.expected_pattern_codes
        assert case.forbidden_new_claims
        assert case.allowed_edit_summary
```

Fixture schema:

```yaml
id: blog_01_meeting_minutes
category: blog
request:
  text: "빠르게 변화하는 디지털 시대에 AI는 단순한 도구를 넘어 업무 혁신의 핵심 파트너가 되었습니다. 이를 통해 더 효율적이고 생산적인 결과를 만들 수 있습니다."
  purpose: "AI 활용 경험 블로그"
  audience: "대학생"
  edit_mode: voice
  voice_samples:
    - "나는 AI를 쓸 때 바로 답부터 달라고 하지 않는다. 먼저 내가 놓친 부분을 질문해 달라고 하는 편이다. 귀찮아 보여도 이 과정을 거치면 계획을 다시 뜯어고칠 일이 줄어든다."
  locked_phrases:
    - "Solar"
context_answers:
  q_metric: "회의록 정리가 40분에서 5분으로 줄었다."
labels:
  locked_values: ["Solar", "40분", "5분"]
  expected_pattern_codes: ["era_background_intro", "beyond_x_to_y"]
  forbidden_new_claims: ["정확도가 95%다", "모든 업무가 자동화됐다"]
  required_meaning: ["회의록 정리 시간이 줄었다"]
  allowed_edit_summary: "과장 서론을 삭제하고 사용자 경험 중심으로 재구성"
```

- [ ] **Step 2: Run integrity tests and verify RED**

```bash
uv run --project apps/api pytest tests/evaluation/test_fixture_integrity.py -v
```

- [ ] **Step 3: Create all 20 labeled fixtures**

Each fixture must contain a real Korean source text of 120~900 characters. The five categories must not reuse the same source by changing only nouns.

- [ ] **Step 4: Implement metrics**

```python
locked_fact_preservation = preserved_locked / total_locked
new_claim_rate = unsupported_new_claims / max(1, output_claims)
pattern_reduction = (bad_patterns_before - bad_patterns_after) / max(1, bad_patterns_before)
voice_constraint_match = matched_constraints / max(1, checked_constraints)
```

Semantic fidelity is stored as 1~5 human/LLM judge score, but a case fails immediately when deterministic preservation fails.

- [ ] **Step 5: Write metric tests**

```python
def test_case_fails_even_with_high_semantic_score_when_number_changes():
    result = EvaluationResult(
        locked_fact_preservation=0.8,
        new_claim_rate=0.0,
        semantic_fidelity=5.0,
        pattern_reduction=0.8,
        voice_constraint_match=0.95,
    )
    assert result.passed is False
```

- [ ] **Step 6: Implement baseline comparison**

Run the same model with three variants:

1. `baseline_plain`: “자연스럽게 다시 써줘”
2. `baseline_rules`: pattern-removal prompt without Claim Locker or Context Interview
3. `owndraft`: full workflow

Use temperature 0.2 and the same model. Save prompt version, model, timestamp, latency, token usage, and case result.

- [ ] **Step 7: Implement CLI and reports**

```bash
uv run --project apps/api python -m owndraft.cli evaluate \
  --cases packages/evaluation/cases \
  --output artifacts/stage1/evaluation-2026-08-28.json \
  --markdown artifacts/stage1/evaluation-2026-08-28.md
```

Exit code 0 only when:

- 20/20 cases executed
- severe locked fact errors = 0
- unsupported new facts = 0
- average pattern reduction >= 0.60
- average semantic fidelity >= 4.5
- voice mode average constraint match >= 0.90

- [ ] **Step 8: Run regression and inspect failures**

```bash
uv run --project apps/api pytest tests/evaluation -v
uv run --project apps/api python -m owndraft.cli evaluate --cases packages/evaluation/cases --output artifacts/stage1/evaluation.json --markdown artifacts/stage1/evaluation.md
```

A failing case is fixed by changing one of: contract, catalog, prompt, verifier, or fixture label. Never delete a difficult case to make the score pass.

- [ ] **Step 9: Commit**

```bash
git add apps/api/src/owndraft/evaluation apps/api/src/owndraft/cli.py packages/evaluation tests/evaluation artifacts/stage1/evaluation.json artifacts/stage1/evaluation.md
git commit -m "test: add 20-case OwnDraft evaluation suite"
```

---

### Task 10: Timely Deployment, Demo Rehearsal, and Submission Freeze

**Files:**
- Create: `docs/stage1/timely-deployment-checklist.md`
- Create: `docs/stage1/demo-script.md`
- Create: `docs/stage1/submission-copy.md`
- Create: `artifacts/stage1/timely-deployment-record.md`
- Create: `artifacts/stage1/final-verification.md`

**Interfaces:**
- Consumes: exported skill, evaluation report
- Produces: deployed Timely skill, reproducible demos, submission evidence

- [ ] **Step 1: Export the frozen candidate**

```bash
uv run --project apps/api python scripts/export_timely_skill.py
shasum -a 256 artifacts/stage1/owndraft-timely-skill.txt
```

Record the digest and 12-character skill version in `timely-deployment-record.md`.

- [ ] **Step 2: Create the Timely skill with fixed metadata**

```text
Name: OwnDraft — 내 말투로 되돌리는 사실 보존형 글 편집기
One-line description: AI 초안의 상투적인 표현을 줄이고 사용자의 실제 경험과 문체를 반영하되 숫자·날짜·이름·출처·핵심 주장을 보존합니다.
Trigger examples:
- 이 AI 초안을 내 말투로 다듬어줘. 사실은 바꾸지 마.
- 이 메일의 날짜와 금액은 유지하면서 자연스럽게 편집해줘.
- 상투적인 AI 표현을 진단하고 실제 경험이 부족하면 질문해줘.
```

Paste the full generated artifact. Store the Timely skill ID or URL, version string, account, and deployment timestamp in the deployment record. Do not store credentials.

- [ ] **Step 3: Run five platform smoke cases**

1. 40분→5분과 Solar 보존
2. 일정 변경 메일의 날짜·시간 보존
3. 예산 요청의 금액·조건 보존
4. 추상적 글에서 질문만 출력하는 분기
5. “AI 탐지 0%로 만들어 달라” 요청을 안전한 편집으로 전환

For each case, record:

```text
input case ID
skill version
first response status
question count
locked facts preserved
new facts
final status
manual reviewer
```

- [ ] **Step 4: Fix only reproducible failures**

A prompt change requires:

```bash
uv run --project apps/api pytest
uv run --project apps/api python -m owndraft.cli evaluate --cases packages/evaluation/cases --output artifacts/stage1/evaluation-final.json --markdown artifacts/stage1/evaluation-final.md
uv run --project apps/api python scripts/export_timely_skill.py
```

Then redeploy and rerun all five smoke cases, not just the failed case.

- [ ] **Step 5: Prepare three fixed demos**

- **Demo A:** AI 활용 블로그 — Context Interview와 40분→5분 보존
- **Demo B:** 업무 메일 — 날짜·금액·담당자 보존과 최소 수정
- **Demo C:** 공모전 소개 글 — 과장 표현 제거와 새 성능 수치 금지

Each script contains source, user answer, expected findings, expected locked values, expected final message, and 30-second explanation.

- [ ] **Step 6: Write submission copy**

The copy must cover:

```text
문제: AI 초안을 받은 뒤 사용자가 상투 표현을 지우고 자신의 경험과 말투를 다시 넣으며 사실을 재확인하는 반복 작업
해결: 사실을 먼저 잠그고, 필요한 경험을 질문한 뒤, 사용자 문체로 편집하고 별도 Critic이 검증
차별점: 한국어 패턴, Claim Locker, Context Interview, one-repair Critic Gate
사회적 가치: AI 사용을 숨기는 대신 사용자의 실제 기여와 변경 과정을 늘리고 투명하게 보여 줌
제외 기능: 워터마크 제거·탐지 우회 보장 없음
```

- [ ] **Step 7: Run final local verification**

```bash
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests scripts
uv run --project apps/api mypy apps/api/src
uv run --project apps/api python scripts/verify_timely_export.py artifacts/stage1/owndraft-timely-skill.txt
```

Copy exact command outputs, evaluation summary, skill digest, and five smoke results into `artifacts/stage1/final-verification.md`.

- [ ] **Step 8: Freeze and tag**

```bash
git add docs/stage1 artifacts/stage1
git commit -m "docs: freeze OwnDraft stage1 submission"
git tag -a stage1-submission-2026-08-31 -m "OwnDraft MABC 2026 stage1 submission"
git status --short
```

Expected: clean working tree.

- [ ] **Step 9: Submit by 2026-08-31 16:00 KST**

Record submission time, representative skill selection, confirmation screenshot filename, and no-change policy after submission.

---

## Final STAGE 1 Verification Checklist

- [ ] 40 pattern rules, unique codes, valid schema
- [ ] 20 evaluation fixtures, four categories with five each
- [ ] locked fact severe errors = 0
- [ ] unsupported new facts = 0
- [ ] average pattern reduction >= 60%
- [ ] average semantic fidelity >= 4.5/5
- [ ] voice constraint match >= 90% when samples are sufficient
- [ ] questions <= 3 and no vague duplicate question
- [ ] one repair maximum
- [ ] detector/watermark request redirect works
- [ ] five Timely smoke cases pass
- [ ] three demos reproducible
- [ ] skill export hash recorded
- [ ] full pytest, Ruff, mypy pass
- [ ] submission confirmation recorded

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-23-owndraft-stage1-skill-implementation.md`.

Execution order is Task 1 through Task 10. The recommended mode is subagent-driven development with a fresh reviewer gate after every task. Inline execution is acceptable only when the same RED→GREEN→full verification→commit sequence is preserved.
