---
title: "A3: 최종 검증 + 배포 판정"
labels: [ready-for-human]
phase: A
size: M
gate: "A 종료 / 배포"
---

# A3: 최종 검증 + 배포 판정

> **게이트 대기:** A1·A2 완료 후 수행. v2 로드맵의 최종 관문.

## What to build

재무·뉴스 확장 후 최종 락박스 검증을 하고, 신호를 앱에 **노출/배포할지** 및
ADR 0008의 **규칙엔진 대체 여부**를 판정한다.

## Acceptance criteria

- [ ] 락박스 **최초 1회만** 개봉
- [ ] deflated Sharpe·n_trials로 과최적화 최종 배제
- [ ] 모델 영속화(재현 가능한 학습·저장) 여부 결정
- [ ] **배포 판정:** 기준선을 락박스에서 마진으로 이기면 라이브 API 노출 재검토
      (v1에서 의도적으로 보류했던 엔드포인트), 아니면 계속 미노출
- [ ] **ADR 0008 재검토:** 규칙엔진 대체/병존 유지 결정을 새 ADR로 기록
- [ ] `docs/ml-signal-limitations.md` v2 갱신(정직한 결과)

## Blocked by

- A1, A2 (필요 시 B 결과와 통합)
