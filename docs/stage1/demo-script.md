# 대표 데모 스크립트 (3개 고정)

각 데모는 원문 → 사용자 답변 → 기대 진단 → 기대 보존값 → 기대 최종 메시지 순서로 구성된다.
모든 데모는 로컬 하네스와 타임리 플랫폼에서 동일하게 재현 가능해야 한다.

---

## Demo A — AI 활용 블로그: Context Interview와 40분→5분 보존

- 케이스 파일: `packages/evaluation/cases/blog_01_meeting_minutes.yaml`
- 원문 요지: "빠르게 변화하는 디지털 시대에는… 단순한 도구를 넘어…" + Solar 언급(수치 없음)
- 1차 응답(기대): `status=needs_context`
  - 질문 예시: "회의록 정리에 실제로 걸리던 시간이 얼마였나요?" (수치형, ≤3개)
  - 재작성본 없음
- 사용자 답변: "회의록 정리 시간은 40분에서 5분으로 줄었다."
- 2차 응답(기대): `status=completed`
  - 기대 진단: era_background_intro, beyond_x_to_y, abstract_positive_effect 제거
  - 기대 보존: Solar, 40분, 5분 (100%)
  - 새 사실: 0개
- 30초 설명: "AI 초안의 상투적 서론을 지우고, 경험이 비어 있으면 질문으로 채운 뒤,
  답변 속 숫자는 잠가 그대로 돌려준다."

## Demo B — 업무 메일: 날짜·금액·담당자 보존과 최소 수정

- 케이스 파일: `packages/evaluation/cases/email_01_schedule_change.yaml` (+ email_02 확장)
- 원문 요지: 회의 일정 변경 안내 — 8월 28일 오후 3시, 회의실 B, kim@example.com
- 응답(기대): `status=completed` (최소 수정 모드)
  - 기대 진단: vague_problem_statement, excessive_hedging 정리
  - 기대 보존: 날짜·시간·장소·이메일·담당자 이름 100%
  - 거동 지시("회신해 주세요") 약화 없음
- 30초 설명: "메일은 표현만 다듬고 사실·기한·수신자 행동은 한 글자도 바꾸지 않는다."

## Demo C — 공모전 소개글: 과장 제거와 새 성능 수치 금지

- 케이스 파일: `packages/evaluation/cases/report_02_competition_proposal.yaml`
- 원문 요지: "업계 유일의… 혁명적인 변화…" + OwnNote, 6개월
- 응답(기대): `status=completed`
  - 기대 진단: promotional_superlative, importance_inflation, chatbot_greeting_closing 제거
  - 기대 보존: OwnNote, 실시간 통역, 6개월 (100%)
  - 새 성능 수치(예: "정확도 95%") 생성 금지 확인
- 30초 설명: "홍보 문장은 걷어내되 근거 없는 수치를 만들지 않는다. 부족한 근거는 지우거나 물어본다."
