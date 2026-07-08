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

- [ ] OHLCV 수집 경로가 수정주가를 반환(또는 조정계수 적용)
- [ ] 피처(`features.py`)·라벨(`labels.py`)이 수정주가 기준으로 계산됨
- [ ] 액면분할이 있던 종목 구간에서 가격 점프가 제거됨을 확인
- [ ] **누수 회귀 테스트:** 수정주가가 과거 시점에 미래 조정계수를 소급 주입하지
      않는지 검증 (조정은 관측 시점 기준이어야 함)
- [ ] 기존 v1 테스트 회귀 없음

## Seam (테스트 필수)

- 고정 분할 시나리오에서 조정 전/후 가격이 예상대로
- 조정계수 소급 주입 방지(미래참조) 회귀

## Blocked by

없음 (Phase D 시작점)
