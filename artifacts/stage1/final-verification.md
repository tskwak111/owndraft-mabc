# STAGE 1 최종 검증 기록 (하드닝 후 재실행)

실행 시각: 2026-08-23 (KST)
실행 위치: 저장소 루트, 브랜치 `agent/owndraft-stage1`
특이사항: 최종 전수 감사에서 발견한 결함 5건 수정 + 회귀 테스트 13건 추가 후 새로 실행

## 1. 최종 감사에서 발견·수정한 결함

| # | 등급 | 내용 | 수정 |
|---|---|---|---|
| D1 | 높음 | Verifier 숫자 검사의 쉼표 비대칭: 클레임 `"1,200,000원"`을 코어 `"1200000"`으로 검색해 동일 숫자 생존 시에도 오타 가능 | `_numeric_present()` 도입 — 구분자 유무 양방향 허용 |
| D2 | 중간 | Locker `_TIME_RE`가 `6시간`→`6시` 클록 시각 오추출(진단 오염) | `(?!간)` lookahead + 회귀 테스트 2건 |
| D3 | 중간 | Upstage 어댑터: (a) 스키마 보정 예산이 인스턴스 전역 공유 (b) OpenAI SDK 내장 재시도(max_retries=2)와 게이트웨이 재시도 이중 동작 | 호출 단위 보정 1회로 구조적 보장 + SDK `max_retries=0` |
| D4 | 낮음 | TraceEvent `input_chars/output_chars` 항상 0 | 실측값 기록(글자 수/개수) + 테스트 강화 |
| D5 | 낮음 | blocked 결과가 폐기된 후보의 change_reasons 노출 / 모델 환각 span_id가 진단에 혼입 | changes=[] 정리 / known_span_ids 필터 |

## 2. 전체 테스트

```bash
$ uv run --project apps/api pytest
======================== 102 passed, 1 skipped in 2.66s =========================
```

- skip 1건: `tests/integration/test_upstage_smoke.py` (UPSTAGE_API_KEY 미제공 — 정당한 skip)
- 신규 테스트 13건: Upstage 어댑터 respx 스위트 6건(성공/보정 1회/보정 소진/429 재시도/429 소진/타임아웃 매핑), Verifier 엣지 6건(쉼표 허용/만원 재표기 거부/단위 변경/날짜 상대화 거부/N시간 정밀도/시각 추출), 진단 환각 필터 1건

## 3. 정적 검사

```bash
$ uv run --project apps/api ruff check apps/api tests scripts
All checks passed!

$ uv run --project apps/api mypy apps/api/src
Success: no issues found in 34 source files
```

- `PatternRule.severity/default_action`을 Literal 타입으로 강화 → scanner의 `type: ignore` 제거

## 4. 평가 실행 (20케이스)

```bash
$ uv run --project apps/api python -m owndraft.cli evaluate \
    --cases packages/evaluation/cases \
    --output artifacts/stage1/evaluation-final.json \
    --markdown artifacts/stage1/evaluation-final.md
OK: 모든 품질 게이트 통과   (exit code = 0)
```

| 지표 | 결과 | 목표 |
|---|---|---|
| 케이스 수 | 20/20 | 정확히 20 |
| 잠긴 사실 심각 오류 | 0 | 0 |
| 지원되지 않는 새 사실 | 0 | 0 |
| 평균 패턴 감소율 | 1.00 | ≥ 0.60 |
| 평균 의미 충실도 | 5.00/5 | ≥ 4.5 |
| voice 제약 일치율 | 1.00 (4개) | ≥ 0.90 |
| repair 초과 | 0 | 0 |

## 5. 타임리 내보내기 결정론 검증

```bash
$ uv run --project apps/api python scripts/export_timely_skill.py
content_sha256: 7ca8ee2b4cbd5c1b305f6905cc4b526ad01009483d7b961174d8c7c3015d5e55
skill_version: 7ca8ee2b4cbd

$ uv run --project apps/api python scripts/verify_timely_export.py artifacts/stage1/owndraft-timely-skill.txt
OK   (exit code = 0)
```

파이썬 코드 수정은 export 원천(SKILL.md·YAML·참조 문서)에 영향이 없어 해시 불변 확인.

## 6. Git 위생

```bash
$ git diff --check   # 통과
$ git status --short # 커밋 후 깨끗함
```

## 7. 안전·프라이버시 확인

- trace에는 상태·지연·글자 수·오류 코드만 기록(테스트로 검증)
- FakeModelGateway는 프롬프트 원문 대신 SHA-256만 기록
- 실제 API 키 미존재; CI는 키 없이 전 게이트 통과하도록 확장(평가+export+verify 포함)

## 8. 남은 수동 단계 (자동화하지 않음)

1. 타임리 플랫폼 스킬 등록 (`docs/stage1/timely-deployment-checklist.md`)
2. 플랫폼 스모크 5케이스 기록 (`timely-deployment-record.md`)
3. ~2026-08-31 16:00 KST 제출 및 확인 화면 기록
4. 선택: UPSTAGE_API_KEY 환경에서 실모델 smoke test 및 실모델 회귀
