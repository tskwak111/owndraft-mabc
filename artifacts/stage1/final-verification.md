# STAGE 1 최종 검증 기록

실행 시각: 2026-08-23 (KST)
실행 위치: 저장소 루트, 브랜치 `agent/owndraft-stage1`, 깨끗한 작업 트리에서 새로 실행

## 1. 전체 테스트

```bash
$ uv run --project apps/api pytest
======================== 89 passed, 1 skipped in 3.17s =========================
```

- skip 1건: `tests/integration/test_upstage_smoke.py` (UPSTAGE_API_KEY 미제공 — 정당한 skip)

## 2. 정적 검사

```bash
$ uv run --project apps/api ruff check apps/api tests scripts
All checks passed!

$ uv run --project apps/api mypy apps/api/src
Success: no issues found in 34 source files
```

## 3. 평가 실행 (20케이스, 품질 게이트)

```bash
$ uv run --project apps/api python -m owndraft.cli evaluate \
    --cases packages/evaluation/cases \
    --output artifacts/stage1/evaluation-final.json \
    --markdown artifacts/stage1/evaluation-final.md
보고서 저장: artifacts/stage1/evaluation-final.json
보고서 저장: artifacts/stage1/evaluation-final.md
OK: 모든 품질 게이트 통과
(exit code = 0)
```

핵심 지표 (`evaluation-final.json`):

| 지표 | 결과 | 목표 |
|---|---|---|
| 케이스 수 | 20/20 | 정확히 20 |
| 완료 | 20 | 20 |
| 잠긴 사실 심각 오류 | 0 | 0 |
| 지원되지 않는 새 사실 | 0 | 0 |
| 평균 패턴 감소율 | 1.00 | ≥ 0.60 |
| 평균 의미 충실도 | 5.00/5 | ≥ 4.5 |
| voice 제약 일치율 | 1.00 (4개 케이스) | ≥ 0.90 |
| repair 초과 케이스 | 0 | 0 |

## 4. 타임리 내보내기와 결정론 검증

```bash
$ uv run --project apps/api python scripts/export_timely_skill.py
exported: /Users/ss020/Dev/owndraft-mabc/artifacts/stage1/owndraft-timely-skill.txt
content_sha256: 7ca8ee2b4cbd5c1b305f6905cc4b526ad01009483d7b961174d8c7c3015d5e55
skill_version: 7ca8ee2b4cbd

$ uv run --project apps/api python scripts/verify_timely_export.py artifacts/stage1/owndraft-timely-skill.txt
OK: 내보내기가 저장소 소스와 일치합니다 (sha256=7ca8ee2b4cbd...)
(exit code = 0)
```

## 5. Git 위생

```bash
$ git diff --check   # 공백 오류 없음
$ git status --short # 커밋 후 깨끗함
```

## 6. 민감 정보 로그 무기록 확인

- trace 이벤트는 상태·지연·글자 수·오류 코드만 포함 (tests/unit/workflow/test_repair.py::test_workflow_records_trace_events_without_sensitive_text)
- FakeModelGateway는 프롬프트 원문 대신 SHA-256 해시만 기록 (tests/unit/llm/test_fake_gateway.py)
- 실제 API 키는 코드·fixture·문서 어디에도 없음 (CI는 키 없이 통과)

## 7. 남은 수동 단계 (자동화하지 않음)

1. 타임리 플랫폼에 스킬 등록 + 붙여넣기 (`docs/stage1/timely-deployment-checklist.md`)
2. 플랫폼 스모크 5케이스 실행 및 `timely-deployment-record.md` 채우기
3. 2026-08-31 16:00 KST 전 제출 및 확인 화면 기록
4. 선택: UPSTAGE_API_KEY 제공 시 실모델 smoke test 실행
