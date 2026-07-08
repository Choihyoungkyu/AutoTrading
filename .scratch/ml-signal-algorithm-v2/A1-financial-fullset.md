---
title: "A1: 재무 피처 풀셋"
labels: [needs-triage]
phase: A
size: M
blocked-by-gate: "C→B/A (C1 승 시 승격)"
---

# A1: 재무 피처 풀셋

> **게이트 대기:** C3에서 C1(재무)이 통과해야 `ready-for-agent`로 승격.

## What to build

C1 min-viable가 통과하면 재무 피처를 풀셋으로 확장한다. 공시 시차를 엄격히 지킨다.

## Acceptance criteria

- [ ] 재무 피처 확장(성장성·수익성·안정성·밸류에이션 등 카테고리별)
- [ ] **공시 시차 엄수:** 각 지표는 실제 공시 가능 시점 이후에만 관측(분기말+45일 기준)
- [ ] 결측·리스테이트먼트(정정공시) 처리 원칙 정의(관측 시점 값 사용)
- [ ] **누수 회귀 테스트** 확장(A1 규모)
- [ ] 확대 후 성과·안정성 리포트

## Blocked by

- C3 (C1 arm 통과 판정)
