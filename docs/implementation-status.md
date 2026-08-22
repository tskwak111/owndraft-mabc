# OwnDraft Implementation Status

## 실행 모드

```text
EXECUTION_TARGET=STAGE_1_ONLY
AUTONOMY=HIGH
REMOTE_WRITE=DISABLED
LIVE_MODEL_TEST=OPTIONAL
```

STAGE 2는 사용자가 명시적으로 `STAGE 2 시작`을 지시할 때까지 시작하지 않는다.

## 저장소 상태

- 브랜치: `agent/owndraft-stage1` (main 기준 생성, 원격 push 없음)
- worktree: 단일 worktree 사용 (저장소 자체가 신규 init이라 별도 worktree 불필요)
- baseline 커밋: 문서 5종 최초 커밋

## 기준 문서 경로와 해시 (SHA-256)

| 파일 | 해시 |
|---|---|
| `OwnDraft_Full_Implementation_Plan.md` | `0a4d165d7dbfc9cae2614f1ae926007a18138579aa6c77fee9711ca0d9db01ab` |
| `docs/superpowers/specs/2026-08-23-owndraft-product-agent-design.md` | `bbfff99885c5b3e8d47105608246d5288c017db94737a8775a54854bedc17767` |
| `docs/superpowers/plans/2026-08-23-owndraft-master-roadmap.md` | `3cebcb3af7e8cff5049fd79eed01dc568518d50eb1ea1c00ea87fcae0285d30d` |
| `docs/superpowers/plans/2026-08-23-owndraft-stage1-skill-implementation.md` | `2d21bb6579208d664b44db84562ed59836ad2ff16f2c3395ec91b4fb68c8ca1e` |
| `docs/superpowers/plans/2026-08-23-owndraft-stage2-mvp-implementation.md` | `60705d3a842701206ab49e0090b77114e560223669bd99a3db268f2b0a97be0b` |

모든 해시는 `MANIFEST.sha256`과 일치한다.

## 문서 충돌 판단 기록

- 설계서 §13.3의 Pattern Scanner 출력 예시(`action: ask_or_rewrite`)와 계획의 `FindingAction`(keep/rewrite/delete/ask) 표현 차이 → 계획의 Literal 타입을 우선한다(우선순위 2).
- **(Task 5)** 계획의 fallback 프로필 테스트 샘플(`"나는 결론부터 말하는 편이다." * 4` = 64자)은 같은 계획이 고정한 확신도 경계(0~79자 → none)와 모순된다. 경계가 핵심 계약이므로 경계를 우선하고 테스트 샘플만 ×6(96자)으로 조정해 low 밴드를 검증한다.
- **(Task 5)** 질문 랭킹 규칙의 해석: 랭킹(source→experience→number→opinion→goal)은 유효 후보가 3개를 넘을 때 생존 선택 기준으로 쓰고, 출력 순서는 원문 후보 입력 순서를 유지한다. 계획의 리터럴 테스트(`["q1","q2","q3"]`)와 양립하는 유일한 해석이다.
- **(Task 7)** 내보내기 검증 테스트가 요구하는 `# 사실 보존 절대 규칙` 헤딩은 고정된 SKILL.md 코어에 없으므로, `safety_policy.md`에 동일 헤딩 섹션을 두어 내보내기가 이를 포함하도록 한다. SKILL.md "exact behavioral core"는 변경하지 않았다.
- **(Task 9)** 오프라인 평가의 의미 충실도·voice 제약 일치율은 결정론적 근사 판정이다(원문+답변 토큰 일치, 자연성 신호). LLM judge 점수와 인간 평가(`human_rating_template.csv`)는 실모델 실행 시 채우는 별도 단계로 남긴다. 사실 보존 판정은 결정론적 Claim Locker 검증이 단독으로 담당한다.
- 나머지 핵심 계약(repair 1회, parse retry 1회, 길이 제한, 확신도 경계)은 문서 간 모순 없음.

## Task 진행 상황 (전부 완료)

| Task | 상태 | 커밋 |
|---|---|---|
| 1. Repository, Typed Settings, and CI Bootstrap | 완료 | `ee16ca8` |
| 2. Stage 1 Contracts, Normalization, and Stable Spans | 완료 | `47154ee` |
| 3. Korean Pattern Catalog and Deterministic Scanner | 완료 | `d528a0b` |
| 4. Claim Locker and Preservation Verifier | 완료 | `e8b7c8a`, `f505f48`(merge 테스트) |
| 5. Voice Profile and Context Question Validation | 완료 | `61aa51c` → typing 수정 포함 `1d859ca` |
| 6. Model Gateway, Upstage Adapter, and Structured Output Parser | 완료 | `2d77dbd` |
| 7. Skill Prompt Pack and Deterministic Timely Export | 완료 | `a39babe` |
| 8. Stage 1 Workflow, Parallel Critics, and One-Repair Gate | 완료 | `ab36b1b` |
| 9. Twenty-Case Evaluation Dataset and Regression Report | 완료 | `a0ce020` |
| 10. Timely Deployment Docs, Demos, Submission Freeze | 완료 | (아래 최종 커밋) |

## 최종 검증 결과 (2026-08-23 새로 실행)

- pytest: **89 passed, 1 skipped** (skip = UPSTAGE_API_KEY 미제공 smoke test)
- ruff check apps/api tests scripts: **All checks passed**
- mypy apps/api/src: **no issues in 34 source files**
- CLI evaluate: exit 0 — 20/20 완료, 심각 오류 0, 새 사실 0, 패턴 감소 100%, 충실도 5.00, voice 100%
- export + verify_timely_export: OK — 스킬 버전 `7ca8ee2b4cbd`
  - content sha256: `7ca8ee2b4cbd5c1b305f6905cc4b526ad01009483d7b961174d8c7c3015d5e55`
- `git diff --check`: 통과

증거 원문: `artifacts/stage1/final-verification.md`

## 알려진 한계 / 리스크

- 평가 리포트의 모델 필드는 `fake-gateway(deterministic)`이다. 실모델(solar-pro4) 회귀는 API 키가 있을 때 별도 실행해야 하며 현재 보고서는 이를 대체하지 않는다.
- 타임리 플랫폼 배포·스모크 5케이스·제출은 수동 미실행 상태 (`timely-deployment-record.md` 참고).
- mismatched_formality/dash_colon_overuse 등 파괴적 제거 위험이 있는 규칙 regex는 픽스처에서 사용하지 않았고, 스캐너 자체는 유지된다.

## 남은 수동 작업

1. 타임리 스킬 등록 및 붙여넣기 (체크리스트 §1)
2. 플랫폼 스모크 5케이스 기록 (§2)
3. 제출 + 확인 화면 기록 (§4)
4. 선택: `UPSTAGE_API_KEY` 환경에서 실모델 smoke test
