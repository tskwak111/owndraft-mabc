# OwnDraft 통합 구현 계획서

> 이 파일은 전체 로드맵, STAGE 1 예선 스킬 구현 계획, STAGE 2 결선 웹 MVP 구현 계획을 실행 순서대로 합친 Codex 전달용 문서다. 세부 요구사항의 기준은 함께 포함된 승인 설계서다.

---

# Part A — 전체 로드맵

# OwnDraft 전체 구현 로드맵

> **기준일:** 2026-08-23  
> **상태:** 제품 설계 승인 후 구현계획 확정  
> **기준 설계서:** `docs/superpowers/specs/2026-08-23-owndraft-product-agent-design.md`  
> **세부 계획:**  
> - `docs/superpowers/plans/2026-08-23-owndraft-stage1-skill-implementation.md`  
> - `docs/superpowers/plans/2026-08-23-owndraft-stage2-mvp-implementation.md`

## 1. 이 로드맵의 목적

OwnDraft를 한 번에 거대한 서비스로 만들지 않는다. 대회 구조와 실패 비용을 기준으로 두 개의 독립적인 구현 단계로 나눈다.

1. **STAGE 1 — 예선:** 타임리 AI에서 실행되는 단일 기능 중심의 글 편집 스킬을 완성한다.
2. **STAGE 2 — 결선:** 예선에서 검증한 Claim Locker, 패턴 카탈로그, 문체 프로필, Critic Gate를 웹 서비스로 확장한다.

예선에서 만든 프롬프트와 평가 데이터는 결선에서 폐기하지 않는다. 모든 핵심 계약과 평가셋을 저장소에 보존하고, 결선 API가 같은 계약을 구현하도록 한다.

---

## 2. 공식 일정에 맞춘 고정 마감

| 게이트 | 절대 마감 | 내부 마감 | 통과 조건 |
|---|---:|---:|---|
| 예선 기능 동결 | 2026-08-30 12:00 KST | 2026-08-29 23:00 | 대표 데모 3개와 20개 평가셋 재현 |
| 예선 제출 | 2026-08-31 18:00 KST | 2026-08-31 16:00 | 타임리 제출 완료·제출 화면 기록 |
| 결선 진출 발표 | 2026-09-07 | 해당 없음 | 결과 확인 후 STAGE 2 착수 여부 결정 |
| 결선 개발 | 2026-09-09~2026-09-18 | 매일 23:00 데일리 동결 | 일별 통합 테스트 통과 |
| 결선 산출물 제출 | 2026-09-18 18:00 KST | 2026-09-18 15:00 | 배포 URL·데모 계정·발표 자료 고정 |
| 오프라인 발표 | 2026-09-19 | 2026-09-18 리허설 완료 | 3분 데모와 장애 대체 영상 준비 |

공식 페이지는 예선에서 단일 기능 중심의 타임리 스킬을 만들고, 결선에서 이를 서비스 MVP로 확장하도록 안내한다. 예선 최종 제출은 8월 31일 18시, 결선 산출물 제출은 9월 18일 18시이며, 오프라인 발표는 9월 19일이다.

---

## 3. 구현 범위 분리

### STAGE 1에서 완성하는 것

- 타임리 AI에 등록할 OwnDraft 스킬 원본
- 한국어 AI 글쓰기 패턴 40개 카탈로그
- 숫자·날짜·인용·링크·사용자 잠금 표현을 보존하는 Claim Locker
- 문체 샘플을 구조화하는 Voice Profile
- 최대 3개의 고가치 질문을 만드는 Context Gap 규칙
- 최소 수정 / 내 말투 수정 모드
- Fact·Fidelity·Voice·Naturalness 검증과 1회 repair
- 20개 고정 평가셋과 비교 실험 하네스
- 대표 데모 3개, 제출 문구, 배포 체크리스트

### STAGE 1에서 제외하는 것

- 로그인과 사용자 계정
- 장기 문체 메모리
- 데이터베이스
- 문장별 승인 UI
- Google Docs·Notion 연동
- AI 탐지기 점수 최적화
- 워터마크 제거 판정

### STAGE 2에서 추가하는 것

- Next.js 웹 편집기
- FastAPI API
- PostgreSQL 기반 문체 프로필·문서 버전·승인 로그 저장
- 익명 세션 기반 사용자 분리
- 문장별 수락·거절·직접 수정
- 승인된 편집만 반영하는 문체 학습
- Contribution Map과 품질 보고서
- 안전한 로그, 암호화 저장, 삭제 흐름
- 배포와 3분 데모

---

## 4. 공통 기술 결정

| 항목 | 결정 | 이유 |
|---|---|---|
| 언어 | Python 3.12, TypeScript, Node.js 24 LTS | 설계서와 일치하고 Next.js 최소 요구사항보다 여유 있게 고정 |
| 백엔드 | FastAPI, Pydantic v2 | 구조화 계약과 테스트가 쉬움 |
| 프런트엔드 | Next.js App Router | 결선 기간 내 편집 UI 구현에 적합 |
| 데이터베이스 | PostgreSQL, pgvector | 문체 샘플과 버전·결정 로그 저장 |
| LLM 연결 | OpenAI 호환 Upstage API | 공식 예제와 동일한 연결 방식 사용 |
| 기본 모델 | 환경 변수 `UPSTAGE_CHAT_MODEL`; 예시값 `solar-pro4` | 플랫폼 제공 모델 변경에 대응하고 코드 하드코딩 방지 |
| 오케스트레이션 | 직접 작성한 명시적 상태 머신 | LangGraph 같은 추가 프레임워크 없이 흐름과 실패 지점을 통제 |
| 테스트 | pytest, Vitest, Playwright | 도메인·API·UI·E2E를 분리 |
| 패키지 관리 | Python `uv`, JavaScript `pnpm` | 잠금 파일 기반 재현성 |
| 관측성 | trace ID, 구조화 로그, 단계별 지연·토큰·검증 결과 | 민감 원문을 로그에 남기지 않고 실패를 추적 |

---

## 5. 구현 전에 고정한 수치 기준

| 기준 | 값 |
|---|---:|
| 예선·결선 원문 최대 길이 | 10,000자 |
| 예선 문체 샘플 개수 | 0~3개 |
| 문체 샘플 절대 최소 총길이 | 80자 |
| 문체 확신도 `low` | 80~159자 |
| 문체 확신도 `medium` | 160~399자 |
| 문체 확신도 `high` | 400자 이상 |
| 사용자 질문 최대 개수 | 3개 |
| 워크플로 repair | 최대 1회 |
| 잠긴 사실 보존 | 100% |
| 새 사실 허용 | 0개 |
| 심각한 의미 왜곡 허용 | 0개 |
| Pattern Reduction 목표 | 60% 이상 |
| 핵심 Voice 제약 일치 | 90% 이상 |
| 예선 평가셋 | 20개 |
| 대표 데모 | 3개 |
| 결선 데모 설명 시간 | 3분 이내 |

`Semantic Fidelity`는 LLM judge 단독으로 통과시키지 않는다. 잠긴 앵커의 결정론적 검사와 함께 사용하며, 5점 척도 평균 4.5 이상을 목표로 한다.

긴 문서는 자동 분할하지 않는다. 10,000자를 넘으면 `document_too_long`으로 거절하고 사용자가 논리 단위로 나누도록 안내한다. 문단 청크 사이에서 부정·조건·인과·사실 잠금이 끊기는 위험을 결선 기간 안에 충분히 검증하기 어렵기 때문이다.

---

## 6. 날짜별 실행 순서

### 2026-08-23 — 계약과 저장소

- [ ] 기준 설계서와 구현계획을 저장소에 넣는다.
- [ ] Python 패키지, 테스트, 린트, CI를 부트스트랩한다.
- [ ] 입력·출력 Pydantic 계약을 고정한다.
- [ ] 첫 번째 smoke fixture를 RED 상태로 만든다.

**종료 게이트:** `pytest`, `ruff`, `mypy`가 빈 뼈대에서 통과하고 계약 스냅샷이 생성된다.

### 2026-08-24 — Pattern Scanner와 Claim Locker

- [ ] 40개 한국어 패턴 YAML을 등록한다.
- [ ] 카탈로그 무결성 테스트를 작성한다.
- [ ] 숫자·날짜·링크·인용·잠금 표현 추출을 구현한다.
- [ ] 보존 비교기를 구현한다.

**종료 게이트:** “40분→5분”, “Solar”, 날짜, 부정문, 직접 인용이 수정본에서 바뀌면 테스트가 실패한다.

### 2026-08-25 — Voice Profile과 Context Interview

- [ ] 문체 샘플 확신도 규칙을 구현한다.
- [ ] 구조화된 Voice Profile 계약을 구현한다.
- [ ] 질문 후보의 중복·모호성·개수 검증을 구현한다.
- [ ] 질문이 필요 없는 보수적 편집 경로를 테스트한다.

**종료 게이트:** 최대 3개·한 질문 한 정보·원문 중복 질문 금지 규칙이 자동 검증된다.

### 2026-08-26 — Solar 호출과 Skill Prompt

- [ ] Upstage OpenAI 호환 어댑터를 구현한다.
- [ ] JSON 출력 파서와 한 번의 파싱 재요청을 구현한다.
- [ ] `SKILL.md`와 참조 파일을 작성한다.
- [ ] 타임리 붙여넣기용 단일 텍스트를 자동 생성한다.

**종료 게이트:** Fake gateway 기반 계약 테스트와 선택적 실제 Solar smoke test가 모두 통과한다.

### 2026-08-27 — Workflow와 Critic Gate

- [ ] 질문 필요 / 바로 재작성의 두 분기를 구현한다.
- [ ] Fact·Fidelity·Voice·Naturalness Critic을 병렬 실행한다.
- [ ] 실패 시 오류만 전달하는 1회 repair를 구현한다.
- [ ] 두 번째 실패 시 원문 유지와 문제 구간 표시를 구현한다.

**종료 게이트:** 정상 통과·repair 통과·repair 실패의 세 경로가 결정론적 테스트로 재현된다.

### 2026-08-28 — 20개 평가셋

- [ ] 블로그·메일·보고서·SNS 각 5개를 고정한다.
- [ ] 일반 재작성 프롬프트와 OwnDraft를 같은 모델로 비교한다.
- [ ] 잠긴 사실 보존, 새 주장, 패턴 감소, 의미 보존 지표를 산출한다.
- [ ] 실패 케이스를 원인별로 분류한다.

**종료 게이트:** 심각한 사실 오류 0개, 새 사실 0개를 만족하지 못하면 제출 프롬프트를 동결하지 않는다.

### 2026-08-29 — 타임리 배포와 데모

- [ ] 생성된 스킬 원문을 타임리에 배포한다.
- [ ] 5개 smoke case를 플랫폼에서 직접 실행한다.
- [ ] 대표 데모 3개를 고정한다.
- [ ] 제출 설명·사용법·차별점 문구를 작성한다.

**종료 게이트:** 로컬 스킬 해시와 타임리 등록본의 버전 문자열이 같고, 3개 데모가 연속 재현된다.

### 2026-08-30 — 기능 동결

- [ ] 프롬프트 변경을 중단한다.
- [ ] 오탈자·정책 문구·입력 누락을 점검한다.
- [ ] 제출 화면과 데모를 녹화한다.
- [ ] 장애 시 보여줄 결과 캡처를 만든다.

**종료 게이트:** `stage1-submission-candidate` 태그 생성, 평가 보고서와 배포 기록 보존.

### 2026-08-31 — 제출

- [ ] 15:00에 타임리 최종 smoke test를 실행한다.
- [ ] 16:00까지 예선 제출을 완료한다.
- [ ] 제출 완료 화면·시간·대표작 설정을 기록한다.
- [ ] 제출 후 스킬 설정을 변경하지 않는다.

### 2026-09-09~2026-09-18 — 결선 MVP

- [ ] 9/9: API·DB·웹 앱 부트스트랩
- [ ] 9/10: 문체 프로필 CRUD와 암호화 저장
- [ ] 9/11: 문서 분석·질문 API
- [ ] 9/12: 재작성 오케스트레이션과 Critic 병렬화
- [ ] 9/13: Diff·결정 API
- [ ] 9/14: 온보딩과 입력 화면
- [ ] 9/15: Diff 승인 UI와 품질 보고서
- [ ] 9/16: 승인 학습·Contribution Map·E2E
- [ ] 9/17: 배포·사용자 테스트·발표 자료
- [ ] 9/18 15:00: 최종 산출물 제출

---

## 7. 품질 게이트

### Gate A — 계약

- 모든 외부 입력과 LLM 출력은 Pydantic으로 검증한다.
- 문자열에서 임의로 필드를 추측하지 않는다.
- 구조화 출력이 깨지면 한 번만 동일 스키마로 재요청한다.
- 두 번째 실패는 사용자에게 부분 실패로 표시한다.

### Gate B — 사실

- 잠긴 숫자와 단위가 모두 존재해야 한다.
- 직접 인용 내용은 공백·문장부호 정규화 외에는 동일해야 한다.
- 부정·조건·예외가 뒤집히면 자동 실패다.
- 새 통계·새 출처·새 경험은 자동 실패다.

### Gate C — 문체

- 문체 샘플이 없으면 “사용자 문체와 일치”를 주장하지 않는다.
- 짧은 샘플은 확신도를 낮게 표시한다.
- 사용자의 말버릇을 매 문장에 반복하지 않는다.
- 글 목적과 충돌하는 구어체는 적용하지 않는다.

### Gate D — 안전

- “워터마크 제거”, “AI 탐지 0%”, “교수에게 안 걸리게”를 목표로 삼지 않는다.
- 요청을 사실·개인 경험·문체 개선으로 전환한다.
- 타인의 고유 문체 복제 요청은 일반 특성으로 추상화한다.
- 의료·법률·금융 고위험 문서는 초기 MVP에서 경고 후 보수적으로 제한한다.

### Gate E — 운영

- 원문과 문체 샘플을 애플리케이션 로그에 남기지 않는다.
- 모든 요청에 trace ID를 부여한다.
- 단계별 지연, 토큰, 실패 코드만 기록한다.
- 배포 전 원문 삭제·프로필 삭제가 실제 DB와 검색 인덱스에서 함께 동작하는지 확인한다.

---

## 8. 팀 규모별 배분

### 혼자 구현할 때

작업 순서를 변경하지 않는다. 하루 종료 전에 완성되지 않은 기능을 다음 기능과 병렬로 벌리지 않는다.

1. 계약·테스트
2. 도메인 로직
3. LLM 연결
4. 평가
5. 타임리 배포
6. 결선 백엔드
7. 결선 프런트엔드
8. 통합·발표

### 2명이 구현할 때

- **A:** Prompt·도메인·백엔드·평가
- **B:** 테스트셋·Timely 검증·프런트엔드·데모

계약 파일과 평가 기준은 A/B가 공동 승인한 뒤 변경한다.

### 3명이 구현할 때

- **A — Agent/Backend:** 계약, Claim Locker, workflow, API
- **B — Evaluation/Prompt:** 패턴 카탈로그, 스킬 프롬프트, 평가셋, 보고서
- **C — Product/Frontend:** Timely 배포, UX, Next.js, 데모·발표

매일 병합 순서는 `contracts → backend → evaluation → frontend`로 고정한다. 계약 변경은 별도 PR로 먼저 병합한다.

---

## 9. 브랜치와 커밋 규칙

- 기본 브랜치: `main`
- 작업 브랜치: `agent/<task-number>-<short-name>`
- 한 작업은 하나의 독립적으로 검토 가능한 결과만 포함한다.
- 커밋 접두어:
  - `feat:` 사용자 기능
  - `fix:` 검증된 오류 수정
  - `test:` 실패 재현·평가셋
  - `docs:` 스킬·설계·데모 문서
  - `chore:` 빌드·CI·의존성
- 프롬프트 변경 커밋에는 평가 보고서 경로를 본문에 기록한다.
- `main` 병합 전 필수 명령:

```bash
uv run --project apps/api pytest
uv run --project apps/api ruff check apps/api tests
uv run --project apps/api mypy apps/api/src
pnpm --dir apps/web test
pnpm --dir apps/web build
```

STAGE 1에는 웹 앱이 없으므로 마지막 두 명령을 실행하지 않는다.

---

## 10. 실패 시 범위 축소 순서

마감이 부족해도 사실 검증을 빼지 않는다. 다음 순서로 범위를 줄인다.

1. 결선의 pgvector 기반 유사 샘플 검색 제거
2. 결선의 프로필 자동 학습 제거, 명시적 수동 반영만 유지
3. 결선의 복수 문체 프로필 UI 제거, 기본 프로필 하나만 유지
4. STAGE 1의 LLM 기반 패턴 40개 전체 진단을 상위 20개 중심으로 축소
5. 대표 데모를 3개에서 2개로 축소

절대 제거하지 않는 것:

- Claim Locker
- 새 사실 0개 게이트
- 최대 3개 질문
- 수정 이유
- 원문·수정문 비교
- 탐지 우회 미보장 정책

---

## 11. 구현 실행 시작 프롬프트

Codex 또는 다른 코딩 에이전트에는 다음 문구로 시작한다.

```text
저장소의 아래 두 문서를 먼저 읽어라.
1. docs/superpowers/specs/2026-08-23-owndraft-product-agent-design.md
2. docs/superpowers/plans/2026-08-23-owndraft-stage1-skill-implementation.md

STAGE 2 파일은 STAGE 1 완료 전 구현하지 마라.
각 Task를 순서대로 처리하고, 반드시 실패 테스트를 먼저 실행한 뒤 최소 구현으로 통과시켜라.
각 Task 종료 시 전체 테스트·lint·type check 결과와 git diff를 검증하고 커밋하라.
프롬프트나 평가 기준을 임의로 완화하지 마라.
잠긴 사실 100% 보존과 새 사실 0개가 최우선이다.
첫 작업은 Task 1뿐이다.
```

---

## 12. 최종 완료 판정

### 예선 완료

- 타임리 제출본이 내부 동결본과 동일한 버전이다.
- 20개 평가셋에서 심각한 사실 오류가 0개다.
- 대표 데모 3개가 플랫폼에서 재현된다.
- 질문·수정·보존 결과가 한 흐름으로 설명된다.
- 탐지 우회·워터마크 제거 보장을 하지 않는다.
- 제출 완료 기록이 남아 있다.

### 결선 완료

- 익명 사용자가 프로필을 만들고 삭제할 수 있다.
- 문서를 분석하고 필요한 질문에 답할 수 있다.
- 수정본과 Diff를 확인하고 문장별 결정을 내릴 수 있다.
- 승인된 편집만 학습 후보가 된다.
- Contribution Map과 품질 보고서가 표시된다.
- 핵심 E2E 3개가 배포 환경에서 통과한다.
- 3분 데모와 장애 대체 영상이 준비되어 있다.


---

# Part B — STAGE 1 예선 스킬

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


---

# Part C — STAGE 2 결선 웹 MVP

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
