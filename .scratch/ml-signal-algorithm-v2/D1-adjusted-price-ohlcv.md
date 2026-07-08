---
title: "D1: 수정주가 반영 OHLCV"
labels: [ready-for-agent]
phase: D
size: M
---

# D1: 수정주가 반영 OHLCV

## What to build

v1은 원본가(raw price)만 사용해 액면분할·증자 구간에서 피처·라벨이 왜곡됐다.
피처·라벨이 **수정주가(adjusted price)** 를 사용하도록 데이터 계약을 정정한다.
이는 검증 신뢰성 문제이므로 Phase D에서 처리한다.

**End-to-end 동작:**
```
get_ohlcv(code, start, end, adjusted=True) -> DataFrame[..., 수정주가 반영]
```

## Acceptance criteria

- [x] OHLCV 수집 경로가 수정주가를 반환(또는 조정계수 적용)
- [x] 피처(`features.py`)·라벨(`labels.py`)이 수정주가 기준으로 계산됨
- [x] 액면분할이 있던 종목 구간에서 가격 점프가 제거됨을 확인
- [x] **누수 회귀 테스트:** 수정주가가 과거 시점에 미래 조정계수를 소급 주입하지
      않는지 검증 (조정은 관측 시점 기준이어야 함)
- [x] 기존 v1 테스트 회귀 없음

## 완료 (2026-07-08)

point-in-time **포워드** 조정으로 구현. pykrx 기본 수정주가(back-adjusted)는 미래
분할이 과거 봉을 소급 변경 → 누수. 대신 원본가에서 분할 이벤트만 추출(`derive_splits`)해
포워드 적용(`adjust_ohlcv`)하여 과거 봉 불변 + 점프 제거를 동시에 달성.

- 신규: `src/ml/prices.py`(`adjust_ohlcv`, `derive_splits`), `tests/test_ml_prices.py`(9 테스트)
- 배선: `run_demo.py` `fetch_pit_ohlcv`가 원본가·back-adjusted 비교로 조정 후 피처·라벨 계산
- 검증: ML 48 테스트 통과, 실데이터 end-to-end 완주(성공=False 유지 — D1은 신뢰성 개선)
- `features.py`/`labels.py` 내부 미변경(조정된 OHLCV를 입력으로 받는 방식, ADR 0008 격리 유지)

## Seam (테스트 필수)

- 고정 분할 시나리오에서 조정 전/후 가격이 예상대로
- 조정계수 소급 주입 방지(미래참조) 회귀

## Blocked by

없음 (Phase D 시작점)
