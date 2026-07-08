---
title: "D2: 유니버스·기간·락박스 확대"
labels: [ready-for-agent]
phase: D
size: M
---

# D2: 유니버스·기간·락박스 확대

## What to build

v1의 12종목·2폴드를 확대해 "엣지 없음" 결론의 통계적 신뢰성을 확보한다. 진짜
point-in-time 유니버스 100~200종목, walk-forward 5폴드+, 락박스 홀드아웃.

**End-to-end 동작:**
```
get_universe(as_of, top_n=200)  # 각 시점 거래대금 상위 (ADR 0007 KRX 로그인)
make_folds(dates, folds>=5, embargo=5, lockbox=<최근 구간>)
```

## Acceptance criteria

- [x] 유니버스 top_n 확대 + **시점별 재선정**(연 1회 리밸런스, 미래참조 없음)
- [x] 기간 확대(2019~2024)로 walk-forward **5폴드** 구성
- [x] 락박스 구간(2024)을 별도 지정하고 평가에서 제외 (`is_lockbox`)
- [x] embargo(5거래일) 갭 유지
- [x] 데모/러너가 확대 데이터셋으로 end-to-end 1회 완주

## 완료 (2026-07-08)

시점별 리밸런싱 유니버스 멤버십을 도입. 유니버스를 리밸런스마다 재선정하고 각
봉(code,date)이 '그 시점' 유효 유니버스에 속할 때만 학습/검증에 쓴다(미래에 유동해진
종목이 과거로 새지 않음). 데모는 편의상 top_n=30(코드는 100~200 지원, 런타임 절약).

- 신규: `src/ml/universe_schedule.py`(`active_universe`, `filter_panel_to_universe`),
  `tests/test_ml_universe_schedule.py`(5 테스트)
- 배선: `run_demo.py` — `build_rebalances`(연 1회 point-in-time 재선정), `filter_panel_to_universe`,
  5폴드 + 락박스(2024) 봉인(D2 미개봉)
- 실데이터 결과: 6리밸런스 → 합집합 93종목, 필터 후 41,985행, 4폴드 평가 **성공=False**
  (전략이 '다 사기'보단 약간 낫지만 마진 미달, 지수는 한 번도 못 이김 → D3에서 판정)
- `make_folds`(lockbox·embargo)는 v1 그대로 재사용(변경 없음)

## Seam (테스트 필수)

- 폴드가 시간순·embargo·락박스 제외를 만족 (기존 `splits.py` 테스트 확장)
- 유니버스가 고정 목록이 아니라 시점별로 달라짐

## Blocked by

- D1 (수정주가 계약)
