# IMPLEMENTATION

구현이 완료된 이슈별 기록 디렉토리.  
각 파일은 이슈 번호로 시작하며, 구현 파일 위치·API 스펙·핵심 로직·테스트 항목을 담는다.

## 목록

| 파일 | 이슈 | 내용 |
|---|---|---|
| [IMPLEMENTATION.md](./IMPLEMENTATION.md) | #001 | 프로젝트 초기화 — 데이터 수집(PYKRX/yfinance)·SQLite 저장소·Flask API |
| [IMPLEMENTATION_002.md](./IMPLEMENTATION_002.md) | #002 | 재무 분석 API — PER/PBR/ROE 등 + 업계 비교·저평가/고평가 판정 |
| [003-samsung-chart.md](./003-samsung-chart.md) | #003 | 기술적 분석 API (MA, RSI, MACD, 볼린저밴드, Buy/Sell 신호) |
| [004-news-analysis.md](./004-news-analysis.md) | #004 | 뉴스 분석 — 네이버+구글+yfinance 멀티소스, 5일·중복제거, 감정 점수 |
| [005-recommendation.md](./005-recommendation.md) | #005 | 종합 추천 엔진 — 재무·차트·뉴스 가중합산 Buy/Hold/Sell |
| [006-price-target.md](./006-price-target.md) | #006 | 목표가·손절 라인 — 현재가 기반 목표/손절/RR 자동 제안 |
| [007-integrated-api.md](./007-integrated-api.md) | #007 | 통합 분석 리포트 API (Primary Seam) — 병렬·캐시·부분실패 |
| [009-multi-stock.md](./009-multi-stock.md) | #009 | 다중 종목 — 종목 검색 API + 반응형 대시보드 전환 |
| [011-price-chart.md](./011-price-chart.md) | #011 | 주가 차트 UI — 일/주/달/년 기간 선택 + Chart.js 시각화 |

## 규칙

- 이슈 완료 시 이 디렉토리에 `{번호}-{slug}.md` 파일 추가
- 원본 이슈는 `.scratch/issues/` 에 그대로 유지
