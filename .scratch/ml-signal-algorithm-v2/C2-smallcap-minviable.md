---
title: "C2: 중소형주 min-viable 실험"
labels: [ready-for-agent]
phase: C
size: S
---

# C2: 중소형주 min-viable 실험

## What to build

저비용 확인: 피처는 차트 전용 그대로 두고 **유니버스만** 저순위 밴드/코스닥으로
교체했을 때 엣지가 생기는지 측정한다. "대형주가 효율적이라 못 이긴다" 가설 검증.

## Acceptance criteria

- [ ] 유니버스를 거래대금 저순위 밴드(예: 200~500위) 또는 코스닥으로 교체
- [ ] 피처·라벨·모델은 v1(차트 전용) 그대로 재사용 — 변수는 유니버스뿐
- [ ] point-in-time 유지(미래참조 없음), 확대된 D2 하네스 재사용
- [ ] 유동성 하한을 둬 극저유동성·슬리피지 왜곡 방지(현실성)
- [ ] 결과를 C3 판정용으로 보고(기준선 대비 마진, 폴드 안정성)

## Seam (테스트 필수)

- 유니버스 밴드 선택이 as_of 시점 데이터만으로 결정됨
- 유동성 하한 필터 경계 동작

## Blocked by

- D3 (D→C 게이트 GO)

## 완료 (2026-07-08) — 결과: 엣지 없음

- 신규: `UniverseSelector.get_universe_band`(랭크 밴드 point-in-time 선정),
  `tests/test_ml_universe_band.py`(9 테스트), `.scratch/ml-signal-algorithm/run_c2_smallcap.py`
- 차트 16피처 그대로, 유니버스만 KOSPI 100~140위 밴드(min_value 5억)로 교체한 A/B.
- 실측: 합집합 176종목·56,317행, **기준선 초과 0/4**, 폴드간 Sharpe -0.82, 성공=False.
- 판정: 중소형주로 바꿔도 차트 엣지 없음("대형주 효율성" 가설 기각). C3에서 종합.
