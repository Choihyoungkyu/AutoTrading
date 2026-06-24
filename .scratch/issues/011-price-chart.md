# 주가 차트 시각화 (일/주/달/년 기간 선택)

## What to build

웹 대시보드에 Chart.js 기반 주가 차트를 추가한다. 일·주·달·년 버튼을 누르면 해당 기간의 종가 추이 그래프가 즉시 그려진다.

**End-to-end 동작:**
- 대시보드 로드 → 기본 '달(1개월)' 차트 자동 표시
- 버튼 클릭 → 해당 기간 데이터 재조회 후 차트 갱신
  - 일: 최근 30 거래일
  - 주: 최근 91일(약 13주)
  - 달: 최근 365일
  - 년: 최근 3년(1095일)

**신규 API 엔드포인트:**
```
GET /api/stock/kr/<code>/price-history?period=1d|1w|1m|1y
→ { "code", "period", "count", "data": [{ date, open, high, low, close, volume, change }] }
```

## Acceptance criteria

- [x] `/api/stock/kr/<code>/price-history` 엔드포인트 구현 (period 파라미터 지원)
- [x] 차트 라이브러리 추가 (Chart.js CDN)
- [x] 주가 차트 카드 UI (달 기본값)
- [x] 일/주/달/년 기간 선택 버튼 (활성 버튼 강조)
- [x] 툴팁: 날짜 + 종가 표시

## Blocked by

- 없음 (PYKRX 엔드포인트는 이미 구현됨)

## 구현일

2026-06-24
