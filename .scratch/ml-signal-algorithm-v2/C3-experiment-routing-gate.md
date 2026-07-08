---
title: "C3: 실험 종합 + B/A 라우팅 게이트 판정"
labels: [ready-for-human]
phase: C
size: S
gate: "C→B/A"
---

# C3: 실험 종합 + B/A 라우팅 게이트 판정

## What to build

C1(재무)·C2(중소형주) 실험 결과를 종합해 어느 방향에 투자할지 판정한다(하드 게이트).

## Acceptance criteria

- [ ] C1·C2 각 arm의 기준선 대비 성과·폴드 안정성을 동일 기준으로 비교
- [ ] **라우팅 판정 문서화:**
  - C1 승 → **A(재무 풀셋) 우선**, A 이슈 승격
  - C2 승 → **B(유니버스 확대) 우선**, B 이슈 승격
  - 둘 다 승 → **B 먼저**(요청 순서 D>C>B>A), 이후 A
  - 둘 다 실패 → **STOP**, 접근 전면 재검토(v1처럼 정직하게 종료)
- [ ] deflated Sharpe·n_trials로 "가짜 승리" 배제

## Gate

산출물은 **판정**이다. 통과한 arm에 해당하는 B 또는 A 이슈를 `needs-triage` →
`ready-for-agent`로 승격한다.

## Blocked by

- C1, C2

## 완료 (2026-07-08) — 판정: **STOP**

C1(재무·대형주)·C2(중소형주·차트) 둘 다 기준선 초과 0/4, 폴드간 Sharpe 음수
(-0.77 / -0.82). 라우팅 규칙상 **둘 다 실패 → STOP, 접근 전면 재검토**.

- B·A로 진행하지 않음. B1·B2·A1·A2는 `needs-triage`로 **동결**.
- 생존 편향이 성능을 낙관적으로 부풀리는 상태인데도 엣지가 없어(B2로도 반전 어려움),
  STOP은 견고한 결론.
- 판정 문서: `docs/ml-signal-v2-c3-gate.md`. 다음은 문제 설정 변경 여부 — 인간 판단.
