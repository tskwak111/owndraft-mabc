# 사실 보존 절대 규칙

OwnDraft가 편집 과정에서 지키는 최소 계약이다. 이 규칙은 원문의 어떤 표현보다 우선한다.

1. 숫자·단위·날짜·시간은 값과 단위를 그대로 유지한다.
   - `40분`을 `약 1시간`, `5분`을 `몇 분`, 특정 날짜를 상대 날짜로 바꾸지 않는다.
2. 사람·회사·기관·제품 이름은 한 글자도 바꾸지 않는다.
3. URL과 이메일 주소는 형태와 대상을 유지한다.
4. 직접 인용은 따옴표 안의 내용을 그대로 보존하거나 삭제만 한다. 의역해 인용하지 않는다.
5. 부정(`~않다`, `아니다`), 조건(`경우`, `때만`, `제외`, `단`), 예외를 긍정으로 뒤집지 않는다.
6. 사용자가 잠금 표현으로 지정한 문자열은 위치와 형태를 유지한다.
7. 새 통계, 새 출처, 새 경험, 새 인용, 새 사실을 만들지 않는다.
8. 위 규칙 위반이 확인되면 결과를 통과시키지 않고 문제 구간을 표시하거나 원문을 유지한다.

# 출력 계약

내부 처리는 아래 세 가지 상태 중 하나로 끝난다.

```text
needs_context : 정보 부족 → 질문까지만 출력
completed     : 사실 보존 검증 통과 → 수정본 출력
blocked       : 검증 실패(수정 2회차) → 원문 유지 + 문제 구간 표시
```

## needs_context 예시

```text
status: needs_context
questions:
  - id: q_metric
    question: "회의록 정리에 실제로 걸리던 시간과 줄어든 시간이 얼마인가요?"
    expected_answer_type: number
```

## completed 예시

```text
status: completed
rewritten_text: "..."
changes:
  - span_id: s_0001
    change_type: delete
    reason: "시대 배경 서론 삭제"
preservation:
    passed: true
    locked_total: 4
    preserved_locked: 4
    new_claim_count: 0
```

## blocked 예시

```text
status: blocked
issues:
  - code: locked_value_missing
    detail: "40분이 수정본에서 사라졌습니다"
recommendation: "원문을 유지하고 사용자에게 확인을 요청하세요"
```

# 진단 신호 체계

한국어 AI 글쓰기 패턴 카탈로그(`pattern_catalog_ko.yaml`)의 40개 코드를 사용한다.
regexes가 있는 규칙은 결정론적으로 탐지하고, regexes가 없는 규칙은 문맥 판단 후에만 보고한다.
문맥상 유지가 정당한 경우 exemptions을 근거로 진단에서 제외할 수 있다.
