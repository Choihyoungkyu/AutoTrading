---
title: "D3: 신뢰성 리포트 + D→C 게이트 판정"
labels: [ready-for-human]
phase: D
size: S
gate: "D→C"
---

# D3: 신뢰성 리포트 + D→C 게이트 판정

## What to build

확대된 데이터셋(D2)으로 백테스트를 돌리고, "엣지 없음"이 통계적으로 믿을 만한지
판정하는 리포트를 낸다. 이 판정으로 Phase C 진행 여부를 결정한다(하드 게이트).

## Acceptance criteria

- [x] 폴드 전반의 성과 **안정성** 리포트(구간별 편차, 승리 폴드 수)
- [x] **n_trials 보고 + deflated Sharpe 보정** (튜닝 반복이 성과를 부풀렸는지)
- [x] 생존 편향으로 성능이 낙관적임을 리포트에 명시
- [x] **GO/STOP 판정 문서화:**
  - 측정이 안정적 + 여전히 엣지 없음 → **GO to C**
  - 확대 표본에서 차트만으로 엣지 발견 → **별도 재평가**(v1 소표본 오판)
  - 측정이 불안정(폴드별 널뛰기) → **STOP**, 하네스 재점검

## 완료 (2026-07-08) — 판정: **GO to C**

- 신규: `src/ml/reliability.py`(`reliability_report`: 폴드 안정성 + deflated Sharpe),
  `tests/test_ml_reliability.py`(5 테스트). `run_demo.py` 판정 섹션이 리포트를 출력.
- 판정 문서: `docs/ml-signal-v2-d3-gate.md`
- 실측: 4폴드 모두 기준선 초과수익 음수(0/4), 평균·Sharpe 음수 → **측정 안정 + 엣지 부재**
  → 설계 게이트 규칙에 따라 **GO to C**. C1·C2 활성화.

## Gate

이 이슈의 산출물은 **판정**이다. GO 시 C1·C2를 착수하고, C 이슈들을 승격한다.

## Blocked by

- D2 (확대 데이터셋)
