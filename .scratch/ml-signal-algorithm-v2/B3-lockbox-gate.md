---
title: "B3: 락박스 검증 + Phase B 게이트 판정"
labels: [ready-for-human]
phase: B
size: S
gate: "B 종료"
---

# B3: 락박스 검증 + Phase B 게이트 판정

> **게이트 대기:** B1·B2 완료 후 수행.

## What to build

유니버스 확대·생존편향 완화 후 엣지가 **락박스(out-of-sample)** 에서 유지되는지
최종 검증하고 판정한다.

## Acceptance criteria

- [ ] 락박스 구간 **최초 1회만** 개봉
- [ ] deflated Sharpe·n_trials로 과최적화 배제
- [ ] **GO/STOP 판정:** 락박스에서 마진으로 이기면 GO(노출/배포 재검토는 A3와 통합),
      아니면 STOP·재설계
- [ ] 생존편향 제거 후 정직한 성과를 문서화

## Blocked by

- B1, B2
