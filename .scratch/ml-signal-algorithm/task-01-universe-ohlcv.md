---
title: "T01: OHLCV 데이터 계약 + point-in-time 유니버스 선정"
labels: [ready-for-agent]
---

# T01: OHLCV 데이터 계약 + point-in-time 유니버스 선정

## What to build

이후 모든 단계(라벨·피처·분할·백테스트)가 의존할 **입력 계약 = "일봉 OHLCV DataFrame"**을 정의하고, 각 결정 시점의 **유동성 상위 ~200 종목 유니버스**를 그 시점 데이터로 재선정한다. 기존 `krx_collector.py`(PYKRX) 위에 얹는다.

**End-to-end 동작:**
```
get_universe(as_of="2022-03-01", top_n=200) -> [종목코드, ...]   # 그 시점 거래대금 상위
get_ohlcv("005930", start, end) -> DataFrame[date, open, high, low, close, volume]
```

## Acceptance criteria

- [ ] 표준 OHLCV DataFrame 스키마 확정(date 인덱스, open/high/low/close/volume 컬럼)
- [ ] `get_universe(as_of, top_n)` — as_of 시점 기준 거래대금/시총 상위 N 종목 반환 (미래 데이터 미사용)
- [ ] 소형주·저유동성 종목 배제로 슬리피지·상폐 리스크 완화
- [ ] 수정주가 사용 시 미래 소급 정보 유입 여부 검토 (원본 가격 + 조정계수 우선)
- [ ] 유니버스가 시점별로 재선정됨(고정 목록 아님)

## Seam

이 태스크는 PYKRX(불순물)를 다루는 유일한 계층. 하위 seam(S1~S4)은 이 출력 DataFrame만 받으므로 이후 목킹 불필요.

## Blocked by

없음 (시작점)

## User Stories

- 7, 8
