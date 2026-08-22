# OwnDraft Implementation Package

이 패키지는 OwnDraft의 승인된 제품 설계와 실행 가능한 구현계획을 한데 묶은 자료다.

## 파일

- `docs/superpowers/specs/2026-08-23-owndraft-product-agent-design.md`  
  제품·에이전트 기준 설계서
- `docs/superpowers/plans/2026-08-23-owndraft-master-roadmap.md`  
  예선부터 결선까지의 일정, 품질 게이트, 팀 배분, 범위 축소 규칙
- `docs/superpowers/plans/2026-08-23-owndraft-stage1-skill-implementation.md`  
  타임리 스킬과 평가 하네스를 만드는 Task 1~10 계획
- `docs/superpowers/plans/2026-08-23-owndraft-stage2-mvp-implementation.md`  
  FastAPI·Next.js 서비스 MVP를 만드는 Task 1~14 계획
- `OwnDraft_Full_Implementation_Plan.md`  
  위 세 계획을 한 파일로 합친 버전

## 실행 순서

1. 기준 설계서를 읽는다.
2. 전체 로드맵에서 일정과 품질 게이트를 확인한다.
3. STAGE 1 계획의 Task 1만 시작한다.
4. 각 Task에서 RED → 최소 구현 → GREEN → 전체 검증 → 커밋 순서를 지킨다.
5. STAGE 1 제출을 동결한 뒤에만 STAGE 2를 실행한다.

## 가장 중요한 기준

- 잠긴 사실 보존 100%
- 새 사실 0개
- 질문 최대 3개
- repair 최대 1회
- AI 탐지 우회와 워터마크 제거 미보장
- 승인되지 않은 모델 결과는 문체 학습에 사용하지 않음

---

# STAGE 1 구현 (완료)

Python 3.12 + Pydantic v2 + Typer 기반 로컬 하네스가 `apps/api`에 있다.
상세 진행 상황과 커밋 목록은 `docs/implementation-status.md`를 참고한다.

## 로컬 설치

```bash
uv sync --project apps/api --all-groups   # 의존성 설치 (실제 API 키 불필요)
```

## 테스트와 정적 검사

```bash
uv run --project apps/api pytest                      # 단위·계약·통합·평가 전체
uv run --project apps/api ruff check apps/api tests scripts
uv run --project apps/api mypy apps/api/src
```

## 선택적 실모델 smoke test (Upstage)

```bash
export UPSTAGE_API_KEY=...            # 실제 키. 코드·fixture에 절대 넣지 않는다.
uv run --project apps/api pytest tests/integration/test_upstage_smoke.py -v
```

키가 없으면 이 테스트는 skip된다. CI와 기본 테스트는 Fake Gateway만으로 완전히 실행된다.
모델명은 환경변수 `UPSTAGE_CHAT_MODEL`(기본 예시 `solar-pro4`)으로 주입한다(`.env.example` 참고).

## 20개 평가셋 실행

```bash
uv run --project apps/api python -m owndraft.cli evaluate \
  --cases packages/evaluation/cases \
  --output artifacts/stage1/evaluation-final.json \
  --markdown artifacts/stage1/evaluation-final.md
# 모든 품질 게이트 통과 시에만 exit code 0
```

## 타임리 스킬 내보내기와 검증

```bash
uv run --project apps/api python scripts/export_timely_skill.py
uv run --project apps/api python scripts/verify_timely_export.py artifacts/stage1/owndraft-timely-skill.txt
```

내보내기는 결정론적이며, 소스(SKILL.md·카탈로그·참조 문서) 변경 시 해시가 바뀐다.

## 타임리 배포·제출 (수동)

`docs/stage1/timely-deployment-checklist.md`와 `artifacts/stage1/timely-deployment-record.md` 참고.
배포와 제출은 자동화하지 않으며 수동 실행 후 기록을 남긴다.

## 안전 경계

OwnDraft는 AI 탐지 우회 도구나 워터마크 제거기가 아니다.

- Claude/Gemini 워터마크 제거나 제거 완료 판정을 하지 않는다.
- Turnitin·GPTZero 등 특정 탐지기 통과를 보장하거나 목표로 하지 않는다.
- "탐지 확률 0%" 주장, 점수 낮출 때까지 반복 재작성을 하지 않는다.
- 사용자 몰래 문체 샘플·생성 결과를 학습 데이터로 사용하지 않는다.
- 새 통계·새 출처·새 경험·새 인용을 임의 생성하지 않는다. 잠긴 앵커는 결정론적으로 검증한다.
