# OwnDraft STAGE 2 Service MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 예선에서 검증한 OwnDraft 파이프라인을 문체 프로필, 문서 버전, 문장별 승인, 승인 기반 학습, Contribution Map을 갖춘 배포 가능한 웹 서비스 MVP로 확장한다.

**Architecture:** Next.js 웹 앱은 익명 세션으로 사용자를 분리하고 FastAPI와 JSON 계약으로 통신한다. FastAPI는 PostgreSQL에 암호화된 문체 샘플과 문서 버전을 저장하며, 예선의 명시적 상태 머신을 재사용해 Claim Locker·Writer·병렬 Critics·Acceptance Gate를 실행한다. 생성과 검증, 저장과 학습을 분리하고 승인된 사용자 결정만 문체 프로필 새 버전의 입력이 된다.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, pgvector, cryptography, structlog, Node.js 24 LTS, Next.js App Router, TypeScript, pnpm, React Testing Library, Vitest, Playwright, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-08-23-owndraft-product-agent-design.md`

## Global Constraints

- 이 계획은 `stage1-submission-2026-08-31` 태그와 20개 평가셋을 입력으로 사용한다.
- 결선 산출물 내부 제출 마감은 2026-09-18 15:00 KST다.
- 마이크로서비스, Redis, 실시간 공동 편집, Google Docs·Notion 연동은 제외한다.
- 기본 인증은 이메일 수집 없는 서명된 익명 세션 쿠키다. `User.email`은 nullable로 유지해 이후 계정 전환을 허용한다.
- 원문은 20자 이상 10,000자 이하로 제한하며 자동 청크 분할은 하지 않는다.
- 원문과 문체 샘플은 애플리케이션 수준에서 암호화해 저장한다.
- 운영 로그에는 원문·수정문·문체 샘플을 기록하지 않는다.
- 승인되지 않은 모델 결과를 문체 학습 데이터로 사용하지 않는다.
- 한 rewrite run은 후보 한 개와 repair 최대 한 번만 생성한다.
- 잠긴 사실 오류, 새 사실, 심각한 의미 왜곡이 있으면 자동 통과하지 않는다.
- API는 `/v1` 아래에서만 공개하며 모든 응답에 `trace_id`를 포함한다.
- 핵심 사용자 흐름은 3분 안에 이해되어야 한다.
- TDD, 독립 Task, 전체 검증, 작은 커밋 규칙을 유지한다.

---

## 1. 최종 파일 구조

```text
owndraft/
├── package.json
├── pnpm-workspace.yaml
├── docker-compose.yml
├── .env.example
├── apps/
│   ├── api/
│   │   ├── alembic.ini
│   │   ├── migrations/
│   │   ├── pyproject.toml
│   │   └── src/owndraft/
│   │       ├── api/
│   │       │   ├── app.py
│   │       │   ├── dependencies.py
│   │       │   ├── middleware.py
│   │       │   ├── schemas/
│   │       │   └── routes/
│   │       ├── core/
│   │       │   ├── settings.py
│   │       │   ├── logging.py
│   │       │   ├── security.py
│   │       │   └── errors.py
│   │       ├── persistence/
│   │       │   ├── base.py
│   │       │   ├── models.py
│   │       │   ├── session.py
│   │       │   └── repositories/
│   │       ├── services/
│   │       │   ├── voice_profiles.py
│   │       │   ├── documents.py
│   │       │   ├── rewrites.py
│   │       │   ├── decisions.py
│   │       │   ├── learning.py
│   │       │   └── quality_reports.py
│   │       └── [STAGE 1 domain packages retained]
│   └── web/
│       ├── app/
│       │   ├── page.tsx
│       │   ├── onboarding/page.tsx
│       │   ├── editor/page.tsx
│       │   └── runs/[runId]/page.tsx
│       ├── components/
│       ├── lib/
│       ├── tests/
│       └── e2e/
├── packages/
│   ├── contracts/
│   │   └── openapi.json
│   └── evaluation/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── .github/workflows/ci.yml
```

---

## 2. 고정 API 계약

### 익명 세션

- 첫 방문에서 백엔드가 `owndraft_session` HttpOnly, SameSite=Lax 쿠키를 발급한다.
- 쿠키에는 랜덤 UUID와 발급 시간을 서명해 넣고 30일 후 만료한다.
- 브라우저 JavaScript는 세션 ID를 직접 읽지 않는다.

### Voice Profile

```http
POST   /v1/voice-profiles
GET    /v1/voice-profiles
GET    /v1/voice-profiles/{profile_id}
PATCH  /v1/voice-profiles/{profile_id}
DELETE /v1/voice-profiles/{profile_id}
POST   /v1/voice-profiles/{profile_id}/learn
```

### Documents and Analysis

```http
POST /v1/documents/analyze
GET  /v1/documents/{document_id}
```

### Rewrite Runs and Decisions

```http
POST /v1/rewrite-runs
GET  /v1/rewrite-runs/{run_id}
POST /v1/rewrite-runs/{run_id}/decisions
GET  /v1/rewrite-runs/{run_id}/quality-report
```

### Required response types

```python
class AnalyzeDocumentResponse(BaseModel):
    document_id: UUID
    version_id: UUID
    claims: list[Claim]
    findings: list[PatternFinding]
    questions: list[ContextQuestion]
    trace_id: str

class RewriteRunResponse(BaseModel):
    run_id: UUID
    status: Literal["running", "completed", "blocked", "failed"]
    input_version_id: UUID
    output_version_id: UUID | None
    rewritten_text: str | None
    diff_spans: list[DiffSpan]
    preservation: PreservationReport | None
    critic_summary: CriticBundle | None
    contribution_map: ContributionMap | None
    trace_id: str
```

---

### Task 1: Promote the Backend to a FastAPI Application

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/src/owndraft/core/settings.py`
- Create: `apps/api/src/owndraft/api/app.py`
- Create: `apps/api/src/owndraft/api/middleware.py`
- Create: `apps/api/src/owndraft/api/dependencies.py`
- Create: `apps/api/src/owndraft/api/routes/health.py`
- Create: `tests/unit/api/test_health.py`
- Create: `tests/unit/api/test_trace_id.py`

**Interfaces:**
- Consumes: STAGE 1 settings and errors
- Produces: `create_app()`, `/health`, trace ID middleware, exception envelope

- [ ] **Step 1: Write failing API tests**

```python
from fastapi.testclient import TestClient
from owndraft.api.app import create_app


def test_health_returns_version_and_trace_id():
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "owndraft-api"
    assert response.headers["x-trace-id"]
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/api/test_health.py -v
```

- [ ] **Step 3: Add backend dependencies**

```toml
"alembic>=1,<2",
"asyncpg>=0.29,<1",
"cryptography>=43,<47",
"fastapi>=0.115,<1",
"httpx>=0.27,<1",
"itsdangerous>=2,<3",
"pgvector>=0.3,<1",
"sqlalchemy[asyncio]>=2,<3",
"structlog>=24,<27",
"uvicorn[standard]>=0.30,<1",
```

- [ ] **Step 4: Implement app factory, safe errors, and trace middleware**

All API errors use:

```json
{
  "error": {
    "code": "contract_error",
    "message": "요청 내용을 확인해 주세요.",
    "details": []
  },
  "trace_id": "trc_4b2d39e2d9304df98c0c61bc46a2ed7a"
}
```

Middleware accepts a valid incoming `X-Trace-ID` only from tests/internal calls; otherwise it generates `trc_<uuid7-or-uuid4>` and returns it in the response header.

- [ ] **Step 5: Verify**

```bash
uv run --project apps/api pytest tests/unit/api -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 6: Commit**

```bash
git add apps/api tests/unit/api
git commit -m "feat: expose OwnDraft FastAPI application"
```

---

### Task 2: PostgreSQL Schema, Migrations, and Repository Boundaries

**Files:**
- Create: `docker-compose.yml`
- Create: `apps/api/alembic.ini`
- Create: `apps/api/migrations/env.py`
- Create: `apps/api/migrations/versions/0001_initial_schema.py`
- Create: `apps/api/src/owndraft/persistence/base.py`
- Create: `apps/api/src/owndraft/persistence/models.py`
- Create: `apps/api/src/owndraft/persistence/session.py`
- Create: `apps/api/src/owndraft/persistence/repositories/protocols.py`
- Create: `tests/integration/persistence/test_schema.py`
- Create: `tests/integration/persistence/test_cascade_delete.py`

**Interfaces:**
- Consumes: settings
- Produces: async session factory, SQLAlchemy models, repository protocols

- [ ] **Step 1: Write integration tests for required tables and cascade behavior**

```python
async def test_initial_schema_contains_all_core_tables(async_engine):
    table_names = await inspect_table_names(async_engine)
    assert set(table_names) >= {
        "users", "voice_profiles", "voice_samples", "documents",
        "document_versions", "claims", "pattern_findings", "rewrite_runs",
        "edit_decisions", "provenance_records",
    }


async def test_deleting_user_removes_profiles_documents_and_embeddings(session):
    user = await seed_user_graph(session)
    await session.delete(user)
    await session.commit()
    assert await count_user_rows(session, user.id) == 0
```

- [ ] **Step 2: Start PostgreSQL and verify RED**

```bash
docker compose up -d db
uv run --project apps/api pytest tests/integration/persistence -v
```

- [ ] **Step 3: Define the database service**

`docker-compose.yml` uses PostgreSQL with pgvector extension, a named volume, a health check, and a test database. No application service is added yet.

- [ ] **Step 4: Implement models with these constraints**

- UUID primary keys
- timezone-aware timestamps
- `users.email` nullable and unique when present
- `voice_profiles(user_id, name, document_type, version)` unique
- `document_versions(document_id, version_no)` unique
- `rewrite_runs.status` check constraint
- encrypted text stored as `BYTEA`, never plaintext `TEXT`
- embeddings stored as vector column when available
- user-owned rows cascade on delete
- audit records retain no plaintext after parent deletion

- [ ] **Step 5: Implement repository protocols**

```python
class VoiceProfileRepository(Protocol):
    async def create(self, user_id: UUID, data: VoiceProfileCreateData) -> VoiceProfileRecord:
        raise NotImplementedError

    async def get(self, user_id: UUID, profile_id: UUID) -> VoiceProfileRecord | None:
        raise NotImplementedError

    async def list(self, user_id: UUID) -> list[VoiceProfileRecord]:
        raise NotImplementedError

    async def save_version(
        self,
        profile_id: UUID,
        profile_json: dict[str, Any],
        confidence: str,
    ) -> VoiceProfileRecord:
        raise NotImplementedError

    async def delete(self, user_id: UUID, profile_id: UUID) -> bool:
        raise NotImplementedError


class DocumentRepository(Protocol):
    async def create_with_original(
        self,
        user_id: UUID,
        data: DocumentCreateData,
        encrypted_content: bytes,
    ) -> DocumentRecord:
        raise NotImplementedError

    async def get_owned(self, user_id: UUID, document_id: UUID) -> DocumentRecord | None:
        raise NotImplementedError

    async def add_version(
        self,
        document_id: UUID,
        source_type: str,
        encrypted_content: bytes,
    ) -> DocumentVersionRecord:
        raise NotImplementedError


class RewriteRunRepository(Protocol):
    async def create_pending(
        self,
        user_id: UUID,
        document_id: UUID,
        idempotency_key: str,
        edit_mode: str,
    ) -> RewriteRunRecord:
        raise NotImplementedError

    async def get_by_idempotency_key(
        self,
        user_id: UUID,
        idempotency_key: str,
    ) -> RewriteRunRecord | None:
        raise NotImplementedError

    async def finish(
        self,
        run_id: UUID,
        status: str,
        output_version_id: UUID | None,
        metrics: dict[str, Any],
    ) -> RewriteRunRecord:
        raise NotImplementedError


class EditDecisionRepository(Protocol):
    async def upsert_many(
        self,
        user_id: UUID,
        run_id: UUID,
        decisions: list[EditDecisionData],
    ) -> list[EditDecisionRecord]:
        raise NotImplementedError

    async def list_active(self, user_id: UUID, run_id: UUID) -> list[EditDecisionRecord]:
        raise NotImplementedError
```

- [ ] **Step 6: Apply migration and verify**

```bash
uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
uv run --project apps/api pytest tests/integration/persistence -v
uv run --project apps/api pytest
```

- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml apps/api/alembic.ini apps/api/migrations apps/api/src/owndraft/persistence tests/integration/persistence
git commit -m "feat: add OwnDraft persistence schema"
```

---

### Task 3: Anonymous Session, Encryption, and Deletion Guarantees

**Files:**
- Create: `apps/api/src/owndraft/core/security.py`
- Create: `apps/api/src/owndraft/services/sessions.py`
- Create: `apps/api/src/owndraft/api/routes/session.py`
- Create: `tests/unit/core/test_encryption.py`
- Create: `tests/unit/services/test_sessions.py`
- Create: `tests/integration/persistence/test_no_plaintext.py`

**Interfaces:**
- Consumes: user repository, settings
- Produces: `TextCipher`, `SessionService`, `get_current_user()`

- [ ] **Step 1: Write encryption round-trip and no-plaintext tests**

```python
def test_text_cipher_round_trip_and_random_nonce(cipher):
    first = cipher.encrypt("내 비공개 문체 샘플")
    second = cipher.encrypt("내 비공개 문체 샘플")
    assert first != second
    assert cipher.decrypt(first) == "내 비공개 문체 샘플"


async def test_voice_sample_is_not_stored_as_plaintext(session, voice_sample_service):
    sample_id = await voice_sample_service.create("내 비공개 문체 샘플")
    raw = await fetch_raw_ciphertext(session, sample_id)
    assert b"비공개" not in raw
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/core/test_encryption.py tests/unit/services/test_sessions.py tests/integration/persistence/test_no_plaintext.py -v
```

- [ ] **Step 3: Implement versioned encryption**

Use Fernet/MultiFernet with `OWNDRAFT_DATA_KEYS` as a comma-separated list of URL-safe keys. Ciphertext envelope:

```text
v1:<key_id>:<fernet_token>
```

The first key encrypts, all configured keys may decrypt. Invalid ciphertext raises `DataDecryptionError` and never returns partial text.

- [ ] **Step 4: Implement anonymous session cookie**

Cookie properties:

```text
name=owndraft_session
HttpOnly=true
SameSite=Lax
Secure=true in production
Max-Age=2592000
Path=/
```

A missing or invalid cookie creates a new user and session. A valid cookie resolves only its own user.

- [ ] **Step 5: Implement deletion**

`DELETE /v1/session` deletes the user graph, clears the cookie, and returns `204`. It must delete embeddings and encrypted blobs through cascade or explicit repository operations.

- [ ] **Step 6: Verify**

```bash
uv run --project apps/api pytest tests/unit/core tests/unit/services/test_sessions.py tests/integration/persistence/test_no_plaintext.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
```

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/owndraft/core/security.py apps/api/src/owndraft/services/sessions.py apps/api/src/owndraft/api/routes/session.py tests
git commit -m "feat: protect user data with anonymous encrypted sessions"
```

---

### Task 4: Voice Profile CRUD and Explicit Profile Generation

**Files:**
- Create: `apps/api/src/owndraft/api/schemas/voice_profiles.py`
- Create: `apps/api/src/owndraft/api/routes/voice_profiles.py`
- Create: `apps/api/src/owndraft/services/voice_profiles.py`
- Create: `apps/api/src/owndraft/persistence/repositories/voice_profiles.py`
- Create: `tests/unit/services/test_voice_profiles.py`
- Create: `tests/integration/api/test_voice_profiles.py`

**Interfaces:**
- Consumes: STAGE 1 voice profiler, cipher, repository
- Produces: five voice profile endpoints and versioned profile records

- [ ] **Step 1: Write service tests**

```python
async def test_profile_creation_encrypts_samples_and_returns_reviewable_profile(service):
    result = await service.create_profile(
        user_id=USER_ID,
        name="개인 블로그",
        document_type="blog",
        samples=[SAMPLE_A, SAMPLE_B, SAMPLE_C],
    )
    assert result.profile.confidence in {"medium", "high"}
    assert result.profile.lexicon.avoided
    assert result.sample_count == 3


async def test_profile_creation_rejects_less_than_80_total_chars(service):
    with pytest.raises(ContractError):
        await service.create_profile(USER_ID, "짧음", "blog", ["너무 짧다"])
```

- [ ] **Step 2: Write API ownership tests**

A user cannot fetch, patch, or delete another session’s profile; return 404 rather than revealing existence.

- [ ] **Step 3: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/services/test_voice_profiles.py tests/integration/api/test_voice_profiles.py -v
```

- [ ] **Step 4: Implement create/list/get/patch/delete**

Create flow:

1. validate 1~3 samples and total length
2. encrypt raw samples
3. call STAGE 1 voice profile operation
4. validate profile contract
5. persist profile version 1 and embeddings
6. return reviewable structured profile without raw samples

PATCH permits name, document type, and user-editable profile fields. It creates a new profile version rather than mutating historical content.

- [ ] **Step 5: Verify and commit**

```bash
uv run --project apps/api pytest tests/unit/services/test_voice_profiles.py tests/integration/api/test_voice_profiles.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
git add apps/api/src/owndraft/api apps/api/src/owndraft/services/voice_profiles.py apps/api/src/owndraft/persistence/repositories/voice_profiles.py tests
git commit -m "feat: manage reviewable voice profiles"
```

---

### Task 5: Document Intake, Analysis, and Context Questions API

**Files:**
- Create: `apps/api/src/owndraft/api/schemas/documents.py`
- Create: `apps/api/src/owndraft/api/routes/documents.py`
- Create: `apps/api/src/owndraft/services/documents.py`
- Create: `apps/api/src/owndraft/persistence/repositories/documents.py`
- Create: `tests/unit/services/test_documents.py`
- Create: `tests/integration/api/test_document_analysis.py`

**Interfaces:**
- Consumes: Claim Locker, Pattern Scanner, Voice Profile repository, Context Gap Analyzer
- Produces: `POST /v1/documents/analyze`, `GET /v1/documents/{id}`

- [ ] **Step 1: Write analysis response tests**

```python
async def test_analyze_persists_original_version_and_returns_questions(client, fake_gateway):
    fake_gateway.set_response("find_context_gaps", QUESTION_BUNDLE)
    response = await client.post("/v1/documents/analyze", json=ABSTRACT_BLOG_REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"]
    assert body["version_id"]
    assert len(body["questions"]) <= 3
    assert body["claims"]
    assert body["trace_id"]
```

- [ ] **Step 2: Test protected spans and 10,000-character limit**

Code blocks, URLs, Markdown links, and quotes must be marked protected. Over-limit input returns 422 with code `document_too_long`.

- [ ] **Step 3: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/services/test_documents.py tests/integration/api/test_document_analysis.py -v
```

- [ ] **Step 4: Implement analysis transaction**

One database transaction persists:

- Document
- original DocumentVersion
- deterministic and model Claims
- deterministic and model PatternFindings
- ContextQuestions as analysis JSON
- safe trace metrics

If a model operation fails, the original document remains stored with status `analysis_failed`; no partial rewrite run is created.

- [ ] **Step 5: Verify and commit**

```bash
uv run --project apps/api pytest tests/unit/services/test_documents.py tests/integration/api/test_document_analysis.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
git add apps/api/src/owndraft/api apps/api/src/owndraft/services/documents.py apps/api/src/owndraft/persistence/repositories/documents.py tests
git commit -m "feat: analyze and persist source documents"
```

---

### Task 6: Persistent Rewrite Runs and Parallel Critic Orchestration

**Files:**
- Create: `apps/api/src/owndraft/api/schemas/rewrite_runs.py`
- Create: `apps/api/src/owndraft/api/routes/rewrite_runs.py`
- Create: `apps/api/src/owndraft/services/rewrites.py`
- Create: `apps/api/src/owndraft/persistence/repositories/rewrite_runs.py`
- Modify: `apps/api/src/owndraft/workflow/stage1.py`
- Create: `tests/unit/services/test_rewrites.py`
- Create: `tests/integration/api/test_rewrite_runs.py`

**Interfaces:**
- Consumes: document analysis, STAGE 1 workflow, database repositories
- Produces: create/get rewrite run endpoints and persisted result

- [ ] **Step 1: Write idempotency and blocked-run tests**

```python
async def test_same_idempotency_key_returns_same_run(client):
    first = await client.post("/v1/rewrite-runs", headers={"Idempotency-Key": "demo-1"}, json=REQUEST)
    second = await client.post("/v1/rewrite-runs", headers={"Idempotency-Key": "demo-1"}, json=REQUEST)
    assert first.json()["run_id"] == second.json()["run_id"]


async def test_failed_fact_gate_persists_blocked_run_without_output_version(client, fake_gateway):
    configure_two_fact_failures(fake_gateway)
    response = await client.post("/v1/rewrite-runs", json=REQUEST)
    assert response.json()["status"] == "blocked"
    assert response.json()["output_version_id"] is None
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/services/test_rewrites.py tests/integration/api/test_rewrite_runs.py -v
```

- [ ] **Step 3: Implement rewrite run lifecycle**

Statuses:

```text
pending -> running -> completed
pending -> running -> blocked
pending -> running -> failed
```

Persist model name, prompt version, total latency, stage latencies, token usage, repair count, and safe error code.

- [ ] **Step 4: Reuse the STAGE 1 state machine**

Refactor only dependency injection and persistence hooks. Do not fork a second workflow implementation. Hooks:

```python
class WorkflowObserver(Protocol):
    async def on_state_completed(self, event: TraceEvent) -> None:
        raise NotImplementedError

    async def on_candidate(self, text: str) -> None:
        raise NotImplementedError

    async def on_finished(self, result: Stage1Result) -> None:
        raise NotImplementedError
```

The observer may persist encrypted content but must not log it.

- [ ] **Step 5: Verify and commit**

```bash
uv run --project apps/api pytest tests/unit/services/test_rewrites.py tests/integration/api/test_rewrite_runs.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
git add apps/api/src/owndraft tests
git commit -m "feat: persist verified rewrite runs"
```

---

### Task 7: Sentence-Level Diff and Edit Decision API

**Files:**
- Create: `apps/api/src/owndraft/contracts/diff.py`
- Create: `apps/api/src/owndraft/services/diffing.py`
- Create: `apps/api/src/owndraft/services/decisions.py`
- Create: `apps/api/src/owndraft/api/schemas/decisions.py`
- Create: `apps/api/src/owndraft/api/routes/decisions.py`
- Create: `apps/api/src/owndraft/persistence/repositories/decisions.py`
- Create: `tests/unit/services/test_diffing.py`
- Create: `tests/integration/api/test_decisions.py`

**Interfaces:**
- Consumes: completed rewrite run
- Produces: stable `DiffSpan` list and decision endpoint

- [ ] **Step 1: Write stable diff tests**

```python
def test_diff_assigns_stable_ids_and_preserves_order():
    diff = create_sentence_diff(
        original="첫 문장입니다. 두 번째 문장입니다.",
        rewritten="첫 문장입니다. 두 번째 문장을 짧게 고쳤습니다.",
    )
    assert [span.id for span in diff] == ["d_0001", "d_0002"]
    assert diff[0].change_type == "unchanged"
    assert diff[1].change_type == "modified"
```

- [ ] **Step 2: Write decision validation tests**

Allowed decisions:

```text
accept
reject
edit
```

- `accept`: final text equals suggested text
- `reject`: final text equals original text
- `edit`: final text is supplied and non-empty
- a span can be changed repeatedly, latest decision is active and history remains
- a user cannot decide another user’s run

- [ ] **Step 3: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/services/test_diffing.py tests/integration/api/test_decisions.py -v
```

- [ ] **Step 4: Implement diff and decisions**

Use sentence spans from the shared segmenter and `difflib.SequenceMatcher` on normalized sentence text. Do not use character-level HTML diff as the canonical data model.

Request:

```json
{
  "decisions": [
    {"span_id": "d_0002", "decision": "edit", "final_text": "직접 고친 문장"}
  ]
}
```

Response returns current accepted document preview and completion ratio.

- [ ] **Step 5: Verify and commit**

```bash
uv run --project apps/api pytest tests/unit/services/test_diffing.py tests/integration/api/test_decisions.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
git add apps/api/src/owndraft tests
git commit -m "feat: support sentence-level edit decisions"
```

---

### Task 8: Explicit Approval Learning and Profile Versioning

**Files:**
- Create: `apps/api/src/owndraft/services/learning.py`
- Create: `apps/api/src/owndraft/contracts/learning.py`
- Modify: `apps/api/src/owndraft/api/routes/voice_profiles.py`
- Create: `tests/unit/services/test_learning.py`
- Create: `tests/integration/api/test_profile_learning.py`

**Interfaces:**
- Consumes: completed decisions and existing profile
- Produces: explicit `/learn` operation and new profile version

- [ ] **Step 1: Write learning safety tests**

```python
async def test_learning_uses_only_accepted_or_user_edited_spans(service):
    candidates = await service.collect_candidates(RUN_WITH_ACCEPT_REJECT_EDIT)
    assert {c.source for c in candidates} == {"accepted", "user_edited"}
    assert all(c.span_id != "rejected_span" for c in candidates)


async def test_learning_requires_explicit_endpoint_call(service):
    await finish_rewrite_without_learning(service)
    assert await profile_version_count(PROFILE_ID) == 1
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/services/test_learning.py tests/integration/api/test_profile_learning.py -v
```

- [ ] **Step 3: Implement learning candidate extraction**

A candidate contains:

```python
class LearningCandidate(BaseModel):
    span_id: str
    source: Literal["accepted", "user_edited"]
    original_text: str
    final_text: str
    document_type: str
    accepted_at: datetime
```

Do not use unchanged spans, rejected spans, or model output without a decision.

- [ ] **Step 4: Implement conservative profile update**

The model receives current profile plus aggregate features, not all raw documents. It may adjust:

- sentence length bucket
- paragraph spacing
- preferred opening
- formality
- punctuation frequency
- preferred/avoided short expressions

Each changed field records evidence count. A field needs evidence from at least three decisions across two documents, except explicit user edits in profile settings.

- [ ] **Step 5: Verify and commit**

```bash
uv run --project apps/api pytest tests/unit/services/test_learning.py tests/integration/api/test_profile_learning.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
git add apps/api/src/owndraft tests
git commit -m "feat: learn voice only from approved edits"
```

---

### Task 9: Contribution Map and Quality Report

**Files:**
- Create: `apps/api/src/owndraft/contracts/quality.py`
- Create: `apps/api/src/owndraft/services/quality_reports.py`
- Create: `apps/api/src/owndraft/api/routes/quality_reports.py`
- Create: `tests/unit/services/test_quality_reports.py`
- Create: `tests/integration/api/test_quality_report.py`

**Interfaces:**
- Consumes: claims, rewrite plan, diff, decisions, critics
- Produces: `ContributionMap`, quality report endpoint

- [ ] **Step 1: Write contribution count tests**

```python
def test_contribution_map_counts_source_and_decisions_without_authorship_claim():
    report = build_contribution_map(FIXTURE)
    assert report.user_supplied_facts == 7
    assert report.user_supplied_experiences == 2
    assert report.model_added_facts == 0
    assert report.model_restructured_sentences == 11
    assert report.user_approved_sentences == 9
    assert "저자 판정" not in report.disclosure_note
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run --project apps/api pytest tests/unit/services/test_quality_reports.py tests/integration/api/test_quality_report.py -v
```

- [ ] **Step 3: Implement report calculations**

Report fields:

```text
user_supplied_facts
user_supplied_experiences
user_supplied_opinions
model_added_facts
model_restructured_sentences
user_approved_sentences
user_edited_sentences
needs_review_sentences
locked_fact_preservation
pattern_reduction
semantic_fidelity
voice_constraint_match
repair_attempts
disclosure_note
```

The disclosure note states that the map is an editing-process record, not proof of human or AI authorship.

- [ ] **Step 4: Verify and commit**

```bash
uv run --project apps/api pytest tests/unit/services/test_quality_reports.py tests/integration/api/test_quality_report.py -v
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
git add apps/api/src/owndraft tests
git commit -m "feat: explain contribution and rewrite quality"
```

---

### Task 10: Next.js App Shell and Typed API Client

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `apps/web/package.json`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/app/globals.css`
- Create: `apps/web/lib/api/client.ts`
- Create: `apps/web/lib/api/types.ts`
- Create: `apps/web/components/AppShell.tsx`
- Create: `apps/web/tests/app-shell.test.tsx`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: OpenAPI schema
- Produces: web shell, typed API client, responsive layout

- [ ] **Step 1: Write the shell test**

```tsx
it("shows the product promise and primary action", () => {
  render(<HomePage />);
  expect(screen.getByRole("heading", { name: /내 생각과 내 말투/ })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /문체 프로필 만들기/ })).toHaveAttribute("href", "/onboarding");
});
```

- [ ] **Step 2: Bootstrap the workspace and verify RED**

```bash
pnpm create next-app@latest apps/web --ts --eslint --app --use-pnpm
pnpm --dir apps/web test
```

Add Vitest and Testing Library before rerunning.

- [ ] **Step 3: Implement the shell**

Navigation:

```text
OwnDraft
새 글 편집
문체 프로필
개인정보 삭제
```

Home sections:

1. one-line promise
2. “사실을 먼저 잠급니다”
3. “필요한 경험만 질문합니다”
4. “바뀐 이유와 보존 결과를 보여 줍니다”
5. detector/watermark non-guarantee note

Do not place fake user counts, fake testimonials, or unsupported performance claims.

- [ ] **Step 4: Generate and consume OpenAPI types**

Export `packages/contracts/openapi.json` from FastAPI and generate TypeScript types. The web app must not manually duplicate enum strings used by the API.

- [ ] **Step 5: Verify build and tests**

Use Node.js 24 in local development and CI. The project must declare `"engines": {"node": ">=20.9"}` and commit `pnpm-lock.yaml`.

```bash
node --version
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web build
```

- [ ] **Step 6: Commit**

```bash
git add package.json pnpm-workspace.yaml apps/web packages/contracts/openapi.json .github/workflows/ci.yml
git commit -m "feat: bootstrap OwnDraft web application"
```

---

### Task 11: Voice Profile Onboarding UI

**Files:**
- Create: `apps/web/app/onboarding/page.tsx`
- Create: `apps/web/components/voice/VoiceSampleForm.tsx`
- Create: `apps/web/components/voice/VoiceProfileReview.tsx`
- Create: `apps/web/lib/validation/voiceSamples.ts`
- Create: `apps/web/tests/voice-onboarding.test.tsx`

**Interfaces:**
- Consumes: voice profile API
- Produces: create/review/edit/delete profile flow

- [ ] **Step 1: Write onboarding interaction tests**

```tsx
it("blocks submission below 80 total characters and explains the threshold", async () => {
  render(<VoiceSampleForm />);
  await user.type(screen.getByLabelText("문체 샘플 1"), "짧은 글");
  expect(screen.getByRole("button", { name: "문체 분석하기" })).toBeDisabled();
  expect(screen.getByText(/80자 이상/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run and verify RED**

```bash
pnpm --dir apps/web test -- voice-onboarding
```

- [ ] **Step 3: Implement three-step onboarding**

1. profile name and document type
2. one to three raw samples with live character count
3. generated profile review with editable chips/controls

The page displays confidence and explains low confidence. Saving is explicit; merely generating a profile does not store it until the user clicks `이 프로필 저장`.

- [ ] **Step 4: Implement delete with clear scope**

Delete copy states that profile, samples, embedding, and future use are removed. Require one confirmation, not a dark pattern.

- [ ] **Step 5: Verify and commit**

```bash
pnpm --dir apps/web test -- voice-onboarding
pnpm --dir apps/web lint
pnpm --dir apps/web build
git add apps/web
git commit -m "feat: add voice profile onboarding"
```

---

### Task 12: Document Editor and Context Question Flow

**Files:**
- Create: `apps/web/app/editor/page.tsx`
- Create: `apps/web/components/editor/DocumentInput.tsx`
- Create: `apps/web/components/editor/EditModeSelector.tsx`
- Create: `apps/web/components/editor/LockedPhraseInput.tsx`
- Create: `apps/web/components/editor/ContextQuestions.tsx`
- Create: `apps/web/tests/document-editor.test.tsx`

**Interfaces:**
- Consumes: document analysis and rewrite APIs
- Produces: intake→analysis→questions→rewrite flow

- [ ] **Step 1: Write editor tests**

```tsx
it("shows context questions before enabling rewrite", async () => {
  server.use(mockAnalyzeWithQuestions());
  render(<EditorPage />);
  await fillDocumentForm();
  await user.click(screen.getByRole("button", { name: "먼저 진단하기" }));

  expect(await screen.findByText(/실제로 줄어든 작업 시간이 있나요/)).toBeInTheDocument();
  expect(screen.queryByText("수정본")).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run and verify RED**

```bash
pnpm --dir apps/web test -- document-editor
```

- [ ] **Step 3: Implement editor form**

Fields:

- source text with 10,000-character counter
- purpose
- audience
- voice profile optional
- minimal/voice mode
- locked phrases chips
- one-time processing toggle, which skips document retention after the run

Primary action is `먼저 진단하기`, not `AI 티 없애기`.

- [ ] **Step 4: Implement question flow**

- show maximum three questions
- one input per question
- allow `건너뛰고 보수적으로 편집`
- preserve answers in browser state until rewrite completes
- disable duplicate submissions while request is active

- [ ] **Step 5: Verify and commit**

```bash
pnpm --dir apps/web test -- document-editor
pnpm --dir apps/web lint
pnpm --dir apps/web build
git add apps/web
git commit -m "feat: add document analysis and context flow"
```

---

### Task 13: Diff Review, Decisions, and Quality Report UI

**Files:**
- Create: `apps/web/app/runs/[runId]/page.tsx`
- Create: `apps/web/components/diff/SideBySideDiff.tsx`
- Create: `apps/web/components/diff/DecisionControls.tsx`
- Create: `apps/web/components/report/PreservationReport.tsx`
- Create: `apps/web/components/report/ContributionMap.tsx`
- Create: `apps/web/tests/rewrite-review.test.tsx`

**Interfaces:**
- Consumes: rewrite run, decisions, quality report APIs
- Produces: final human review experience

- [ ] **Step 1: Write review behavior tests**

```tsx
it("accepts, rejects, and edits sentence suggestions", async () => {
  render(<RewriteReviewPage runId="run-1" />);
  await screen.findByText("원문");
  await user.click(screen.getAllByRole("button", { name: "수락" })[0]);
  await user.click(screen.getAllByRole("button", { name: "거절" })[1]);
  await user.click(screen.getAllByRole("button", { name: "직접 수정" })[2]);
  await user.type(screen.getByRole("textbox", { name: "최종 문장" }), "내가 직접 고친 문장");
  expect(screen.getByText(/3개 중 3개 검토/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run and verify RED**

```bash
pnpm --dir apps/web test -- rewrite-review
```

- [ ] **Step 3: Implement side-by-side sentence review**

Desktop: original left, suggestion right. Mobile: stacked cards. Each modified span shows:

- original
- suggestion
- concise reason
- protected facts used
- accept/reject/edit controls

Unchanged spans are collapsed by default.

- [ ] **Step 4: Implement reports**

Preservation Report displays explicit values:

```text
이름·기관·제품: 유지
숫자·날짜·단위: 유지
출처·직접 인용: 새로 추가 없음
새 사실: 0개
repair: 0회 또는 1회
```

Contribution Map includes the required disclosure that it is not an authorship detector.

- [ ] **Step 5: Add explicit learning action**

`이 선택을 문체 프로필에 반영` is unchecked by default and only enabled when a profile exists and at least one accepted or edited span exists.

- [ ] **Step 6: Verify and commit**

```bash
pnpm --dir apps/web test -- rewrite-review
pnpm --dir apps/web lint
pnpm --dir apps/web build
git add apps/web
git commit -m "feat: review diffs and explain rewrite quality"
```

---

### Task 14: Observability, End-to-End Tests, Deployment, and Demo Freeze

**Files:**
- Create: `apps/api/src/owndraft/core/logging.py`
- Modify: `apps/api/src/owndraft/api/middleware.py`
- Create: `apps/web/e2e/voice-profile.spec.ts`
- Create: `apps/web/e2e/context-rewrite.spec.ts`
- Create: `apps/web/e2e/privacy-delete.spec.ts`
- Create: `scripts/seed_demo.py`
- Create: `docs/stage2/deployment.md`
- Create: `docs/stage2/demo-script.md`
- Create: `docs/stage2/privacy-notice.md`
- Create: `artifacts/stage2/final-verification.md`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: complete API and web app
- Produces: deployable service, three E2E flows, demo data, final evidence

- [ ] **Step 1: Write log redaction tests**

```python
def test_structured_log_never_contains_source_text(caplog):
    log_workflow_event(
        trace_id="trc_1",
        source_text="매우 민감한 원문",
        state="candidate",
        latency_ms=1200,
    )
    assert "민감한 원문" not in caplog.text
    assert "source_chars" in caplog.text
```

- [ ] **Step 2: Implement safe structured logging**

Allowed fields:

```text
trace_id
user_hash
document_id
run_id
state
latency_ms
input_chars
output_chars
model
prompt_version
input_tokens
output_tokens
repair_attempts
critic_passed
error_code
```

Forbidden fields include source text, rewritten text, sample text, context answers, raw model response, cookie value, API key.

- [ ] **Step 3: Write three Playwright E2E tests**

1. create and delete voice profile
2. analyze abstract draft, answer one context question, receive completed rewrite, accept/edit decisions
3. delete session and verify prior resource URLs return 404

Use a fake model gateway in CI and one optional deployed-environment smoke suite with real Solar.

- [ ] **Step 4: Run complete local stack**

```bash
docker compose up -d db
uv run --project apps/api uvicorn owndraft.api.app:create_app --factory --host 0.0.0.0 --port 8000
pnpm --dir apps/web dev
pnpm --dir apps/web playwright test
```

- [ ] **Step 5: Add demo seed data**

`seed_demo.py` creates three profiles/documents using encrypted storage:

- 블로그 40분→5분 demo
- 일정·금액 보존 email demo
- 공모전 소개 글 demo

The script is idempotent and prints IDs but no plaintext after seeding.

- [ ] **Step 6: Deploy with environment separation**

Required secrets:

```text
UPSTAGE_API_KEY
UPSTAGE_BASE_URL
UPSTAGE_CHAT_MODEL
DATABASE_URL
OWNDRAFT_DATA_KEYS
OWNDRAFT_SESSION_SECRET
APP_ENV=production
WEB_ORIGIN
```

Run migrations exactly once before exposing the web app. Set HTTPS-only cookies and CORS to the single production origin.

- [ ] **Step 7: Run final verification**

```bash
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests scripts
uv run --project apps/api mypy apps/api/src
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web build
pnpm --dir apps/web playwright test
```

Then run the deployed smoke matrix for three demos and record URL, commit SHA, migration revision, model, prompt version, p50/p95 latency, and screenshots in `artifacts/stage2/final-verification.md`.

- [ ] **Step 8: Prepare the three-minute demo**

```text
0:00~0:25 문제: AI 초안 뒤의 반복 수정 작업
0:25~0:50 문체 프로필과 사실 잠금
0:50~1:20 추상적 원문 진단과 한 개 맥락 질문
1:20~1:55 수정본·Diff·사실 보존 결과
1:55~2:20 문장별 수락·직접 수정
2:20~2:40 승인 기반 학습과 Contribution Map
2:40~3:00 차별점·사회적 가치·제외 기능
```

Prepare a local backup recording and static screenshots for network failure.

- [ ] **Step 9: Freeze and tag**

```bash
git add .
git commit -m "docs: freeze OwnDraft stage2 MVP"
git tag -a stage2-final-2026-09-18 -m "OwnDraft MABC 2026 final MVP"
git status --short
```

Expected: clean working tree and all verification commands recorded with exit code 0.

---

## Final STAGE 2 Verification Checklist

- [ ] voice profile create/review/edit/delete
- [ ] encrypted sample and document storage
- [ ] anonymous session isolation
- [ ] document analysis and maximum three questions
- [ ] persistent rewrite run with one repair maximum
- [ ] sentence-level accept/reject/edit
- [ ] explicit-only profile learning
- [ ] Contribution Map and preservation report
- [ ] no raw text in logs
- [ ] session deletion removes all owned data
- [ ] full backend tests, Ruff, mypy pass
- [ ] web unit tests, lint, build pass
- [ ] three Playwright E2E tests pass
- [ ] three deployed demos reproduce
- [ ] three-minute demo and backup recording ready
- [ ] production URL, commit SHA, migration, model, prompt version recorded

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-23-owndraft-stage2-mvp-implementation.md`.

Do not execute this plan before STAGE 1 is frozen and the contest confirms progression to the service-MVP phase. Execute Task 1 through Task 14 in order, with a reviewer gate after each task and full end-to-end verification before the final tag.
