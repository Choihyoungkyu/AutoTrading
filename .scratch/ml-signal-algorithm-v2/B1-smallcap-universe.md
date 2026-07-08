---
title: "B1: 중소형주 유니버스 확대"
labels: [needs-triage]
phase: B
size: M
blocked-by-gate: "C→B/A (C2 승 시 승격)"
---

# B1: 중소형주 유니버스 확대

> **게이트 대기:** C3에서 C2(중소형주)가 통과해야 `ready-for-agent`로 승격.

## What to build

C2 min-viable 실험이 통과하면, 중소형주 유니버스를 풀 규모로 확대해 엣지가
규모에서도 유지되는지 본다.

## Acceptance criteria

- [ ] 중소형주/코스닥 유니버스를 풀 규모로 확대(point-in-time 유지)
- [ ] 유동성·슬리피지 현실 가정 반영(거래비용·체결 가능성)
- [ ] 확대 후에도 폴드 전반 성과 안정성 리포트

## Blocked by

- C3 (C2 arm 통과 판정)
