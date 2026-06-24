# 다중 종목 지원 (NAVER, SK Hynix 등)

## What to build

삼성전자(005930)뿐만 아니라 다른 종목도 분석할 수 있게 확장한다. 종목 검색 기능을 추가하여 사용자가 관심 있는 어떤 종목이든 빠르게 분석받을 수 있게 한다.

**End-to-end 동작:**
```
대시보드 종목 입력창에 "000660" (SK Hynix) 입력
→ 즉시 SK Hynix 분석 결과 표시

또는

GET /search?q=naver
→
[
  { "code": "035420", "name": "네이버", "market": "KOSPI" },
  { "code": "108320", "name": "네이버", "market": "ETF" }
]
```

## Acceptance criteria

- [ ] 종목 검색 엔드포인트 구현 (`GET /search?q=<keyword>`)
  - PYKRX 또는 사전 데이터로 종목명 검색
  - 상위 5개 결과 반환
- [ ] 대시보드에 종목 검색 UI 추가 (자동완성 또는 드롭다운)
- [ ] 국내 주식 5개 이상(NAVER, SK Hynix, SKHC, LG화학 등)으로 `/analyze/<code>` 테스트 완료
- [ ] 해외 주식 지원 (선택사항)
  - AAPL, TSLA, MSFT 등 `/analyze/AAPL` 가능
- [ ] 모든 종목에서 동일한 분석 결과 구조 반환
- [ ] 종목별 분석 결과 캐싱 (같은 종목 재조회 빠름)
- [ ] 통합 API 및 대시보드에서 다중 종목 처리 테스트

## Blocked by

- 007: 통합 분석 리포트 API (Primary Seam)
- 008: 웹 대시보드 UI (삼성전자 리포트)

## User Stories

- 1~11: 모든 종목에 적용 가능
- 12: 국내 주식뿐 아니라 해외 주식도 분석 가능 (우수 기능)
