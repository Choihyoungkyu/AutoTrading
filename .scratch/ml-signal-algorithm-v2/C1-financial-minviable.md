---
title: "C1: 재무 min-viable 실험"
labels: [ready-for-agent]
phase: C
size: M
---

# C1: 재무 min-viable 실험

## What to build

큰 투자 전 저비용 확인: 소수의 재무 피처를 **공시 시차**를 지켜 추가했을 때
차트 전용 대비 엣지가 생기는지 격리 측정한다. 대형주 유니버스 유지.

## Acceptance criteria

- [ ] 재무 피처 소수(예: PER·PBR·ROE 등 3~5개)만 추가 (풀셋은 A1)
- [ ] **공시 시차 엄수:** 분기 실적은 분기말+45일 이후에만 관측 가능(미래참조 금지)
- [ ] 차트 전용 대비 **격리 측정**(재무 arm vs 차트 baseline)을 동일 하네스로
- [ ] **누수 회귀 테스트:** 특정 시점에 아직 공시 안 된 재무가 새지 않는지
- [ ] 결과를 C3 판정용으로 보고(기준선 대비 마진, 폴드 안정성)

## Seam (테스트 필수)

- 공시 시차 경계(분기말+44일 vs +45일)에서 재무 관측 여부가 옳게 갈림
- 재무 피처 결합 후에도 T-불변성 유지

## Blocked by

- D3 (D→C 게이트 GO)

## 완료 (2026-07-08) — 결과: 엣지 없음

- 신규: `src/ml/fundamentals.py`(`join_fundamentals_asof`, merge_asof backward로 공시 시차 엄수),
  `tests/test_ml_fundamentals.py`(누수 회귀 포함 3 테스트), `.scratch/ml-signal-algorithm/run_c1_financial.py`
- 재무 피처 4개(fund_per/pbr/div/earnings_yield)를 D 대형주에 추가한 A/B.
- 실측: 합집합 93종목·33,735행, **기준선 초과 0/4**, 폴드간 Sharpe -0.77, 성공=False.
- 판정: 재무 추가로도 대형주 엣지 없음. C3에서 종합.
