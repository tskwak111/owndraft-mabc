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
