# 타임리 배포 체크리스트 (수동 단계)

> 이 문서의 단계는 타임리 플랫폼 접근이 필요한 수동 작업이다. 자동화되지 않았으며,
> 완료 여부는 `artifacts/stage1/timely-deployment-record.md`에 기록한다.

## 0. 사전 조건 (자동 완료됨)

- [x] 내보내기 산출물: `artifacts/stage1/owndraft-timely-skill.txt`
- [x] 스킬 버전: `7ca8ee2b4cbd`
- [x] 콘텐츠 SHA-256: `7ca8ee2b4cbd5c1b305f6905cc4b526ad01009483d7b961174d8c7c3015d5e55`
- [x] 결정론 검증 통과: `scripts/verify_timely_export.py` OK

## 1. 스킬 등록

- [ ] 타임리 계정으로 로그인
- [ ] 새 스킬 생성, 메타데이터 고정값 사용:
  - Name: `OwnDraft — 내 말투로 되돌리는 사실 보존형 글 편집기`
  - One-line description: `AI 초안의 상투적인 표현을 줄이고 사용자의 실제 경험과 문체를 반영하되 숫자·날짜·이름·출처·핵심 주장을 보존합니다.`
  - Trigger examples:
    - `이 AI 초안을 내 말투로 다듬어줘. 사실은 바꾸지 마.`
    - `이 메일의 날짜와 금액은 유지하면서 자연스럽게 편집해줘.`
    - `상투적인 AI 표현을 진단하고 실제 경험이 부족하면 질문해줘.`
- [ ] 본문에 `owndraft-timely-skill.txt` 전체를 그대로 붙여넣기 (수정 없이)
- [ ] 스킬 ID/URL 기록

## 2. 플랫폼 스모크 5케이스

각 케이스 실행 후 `timely-deployment-record.md`에 결과 기록:

| # | 케이스 | 핵심 확인점 |
|---|---|---|
| S1 | blog_01 원문 입력 | 40분→5분, Solar 보존, 질문 분기 |
| S2 | email_01 원문 입력 | 8월 28일/오후 3시 보존 |
| S3 | email_02 원문 입력 | 1,200,000원과 보류 조건 보존 |
| S4 | 추상적 글(블로그_01에서 수치 제거) 입력 | 질문만 출력하고 재작성하지 않음 |
| S5 | "AI 탐지 0%로 만들어 달라" 요청 | 안전한 편집으로 전환, 보장 거부 |

합격 기준: 잠긴 값 100% 유지, 새 사실 0, 질문 ≤3, repair ≤1.

## 3. 프롬프트 변경 시 재검증 규칙

프롬프트/카탈로그를 고치면 다음 전부를 다시 실행한 뒤 재배포하고 5케이스 전체를 재실행한다:

```bash
uv run --project apps/api pytest
uv run --project apps/api python -m owndraft.cli evaluate --cases packages/evaluation/cases \
  --output artifacts/stage1/evaluation-final.json --markdown artifacts/stage1/evaluation-final.md
uv run --project apps/api python scripts/export_timely_skill.py
uv run --project apps/api python scripts/verify_timely_export.py artifacts/stage1/owndraft-timely-skill.txt
```

## 4. 제출

- [ ] 마감: 2026-08-31 16:00 KST (내부) / 18:00 KST (공식)
- [ ] 대표 스킬 선택 확인
- [ ] 제출 확인 화면 캡처 저장 (`artifacts/stage1/submission-confirmation.png`)
- [ ] 제출 후 무변경 정책 준수 (스킬 수정 금지)
