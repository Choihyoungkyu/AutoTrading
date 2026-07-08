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
