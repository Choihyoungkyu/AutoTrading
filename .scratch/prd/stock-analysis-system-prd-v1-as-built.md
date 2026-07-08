---
title: "주식 분석 시스템 (Stock Analysis System) — V1 As-Built PRD"
labels: [ready-for-human]
created: 2026-07-08
status: implemented
supersedes-planning: stock-analysis-system-prd.md
---

# 주식 분석 시스템 — V1 As-Built PRD

> 본 문서는 **계획 PRD**([stock-analysis-system-prd.md](./stock-analysis-system-prd.md))가 아니라,
> **2026-07-08 기준 실제 개발이 완료된 내용**을 정리한 As-Built PRD다.
> "무엇을 만들 것인가"가 아니라 **"무엇을 만들었는가"**를 서술한다.

---

## 1. 핵심 네러티브

월급의 30%를 주식에 투자하는 직장인은 "괜찮은 기업 같으니까" 매수하고, 주가가 흔들리면 불안해서 손절하고, 오르는 종목은 놓칠까 봐 과도하게 담는다. 진짜 문제는 정보 부족이 아니라 **의사결정이 늦고, 감정에 휘둘린다**는 것이었다.

**주식 분석 시스템 V1**은 종목 코드/이름 하나로 재무·차트·뉴스를 자동 수집·해석하고, **객관적 매수/매도/관망 신호**와 **목표가·손절가**를 한 화면에 제시한다. 정보의 양이 아니라 **빠른 판단과 감정 제거**에 베팅한다.

- **범위 원칙**: V1은 **분석·추천까지만** 한다. 주문·체결(자동매매)은 V2 영역이다.

---

## 2. 타겟 사용자

**개인 투자자 (정보 분석에 시간·도구가 부족한 직장인)**
- 직접 종목을 고르고 매매하지만 분석에 쓸 시간이 부족하다.
- 재무·차트·뉴스를 한 화면에서 보고, 종합 리포트로 5분 안에 판단하고 싶다.
- 재무제표·차트 분석 경험이 없어도 시스템이 해석해서 신호로 전달해주길 원한다.

---

## 3. 구현 완료 기능 (V1)

각 기능은 이슈 단위로 구현되었고, 상세 구현 기록은 [`IMPLEMENTATION/`](../../IMPLEMENTATION/)에 있다.

| # | 기능 | 상태 | 요약 |
|---|---|:---:|---|
| 001 | **데이터 수집·저장** | ✅ | PYKRX(국내)·yfinance(해외) 시세 수집, SQLite 캐시, Flask API 골격 |
| 002 | **재무 분석** | ✅ | PER·PBR·ROE·EPS·부채비율·배당 + 업종 중앙값 비교 → 저평가/고평가 판정 |
| 003 | **기술적 분석** | ✅ | MA·RSI·MACD·볼린저밴드·거래량 → 룰 기반 Buy/Hold/Sell 신호 |
| 004 | **뉴스 분석** | ✅ | 네이버+구글+yfinance 멀티소스, 최근 5일·중복 제거, 키워드 감정 점수 |
| 005 | **종합 추천** | ✅ | 재무·차트·뉴스 가중 합산(30/40/30%) → Buy/Hold/Sell + 사유 |
| 006 | **목표가·손절** | ✅ | 현재가 기반 목표가·손절가·리스크리워드(RR) 비율, 기대수익률/손실률 조절 |
| 007 | **통합 리포트 API** | ✅ | `/analyze/<code>` 한 번에 전체 통합 — 병렬 수집·캐시·부분 실패 허용 |
| 008 | **대시보드 UI** | ✅ | Vue 3 SPA, 항목별 탭 구성, Chart.js 시각화 |
| 009 | **다중 종목** | ✅ | 종목 검색(자동완성) → 어떤 국내 종목이든 대시보드 전환 |
| 010 | **관심 종목** | ✅ | 관심 종목 등록·패널 관리 (로컬 상태) |
| 011 | **주가 차트** | ✅ | 일/주/달/년 기간 선택 + 이동평균·볼린저밴드 오버레이 + 등락률·OHLC 표시 |
| — | **홈 화면 / 업종별 재무평균 / 시장지수** | ✅ | 홈 뷰, 업종별 재무 평균 비교, 시장 지수(MarketIndices) 카드 |

### 기능별 상세

**① 재무 분석 (기업)** — `src/analyzers/financial_analyzer.py`
PER·PBR·ROE·EPS·부채비율·배당수익률을 계산하고 **동종 업종 중앙값과 비교**해 저평가/고평가 시그널을 낸다. 국내 재무 지표는 PYKRX `get_market_fundamental`(KRX 로그인 필요)을 쓰며, 부채비율은 별도재무 이슈로 yfinance를 병행한다(ADR 0005). 재무 결과는 일 단위로 캐싱된다.

**② 기술적 분석 (차트)** — `src/analyzers/chart_analyzer.py`
OHLCV 시세로 이동평균선·RSI·MACD·볼린저밴드·거래량을 계산하고 **룰 기반으로 매수/관망/매도 신호**를 산출한다.

**③ 뉴스 분석** — `src/analyzers/news_analyzer.py`, `src/collectors/news_collector.py`
네이버·구글·yfinance 멀티소스로 최근 5일 헤드라인을 수집하고 중복을 제거한 뒤 **키워드 룰(호재/악재 사전)**로 감정 점수를 매긴다. (ML/감성분석이 아니라 단순 키워드 룰 — 정확도보다 동작 우선.)

**④ 종합 추천** — `src/analyzers/recommendation_engine.py`
재무·차트·뉴스 점수를 **가중 합산(30% / 40% / 30%)**해 Buy/Hold/Sell과 **판단 사유**를 낸다.

**⑤ 목표가·손절** — `src/analyzers/price_target_calculator.py`
현재가 기반으로 목표가 = 현재가 × (1 + 기대수익률), 손절가 = 현재가 × (1 − 허용손실률), **리스크리워드 비율**을 제안한다. 기대수익률·허용손실률은 파라미터로 조절 가능.

**⑥ 통합 리포트 (Primary Seam)** — `src/api/routes.py`
`GET /analyze/<code>` 하나로 재무·차트·뉴스·추천·목표가를 병렬 수집해 한 번에 반환한다. **부분 실패 허용**(일부 소스 실패 시 나머지로 리포트 구성) + 캐시.

**⑦ 대시보드** — `frontend/`
Vue 3 (Vite) SPA. 종합 추천 · 목표가·손절 · 개요 · 주가 차트 · 재무 · 기술적 분석 · 뉴스 **탭**으로 구성. Chart.js 시각화, 종목 검색 자동완성, 관심 종목 패널, 홈 화면, 업종별 재무 평균, 시장 지수 카드. 모바일-퍼스트 반응형(모바일/태블릿/데스크탑).

---

## 4. API 엔드포인트 (구현 완료)

| 메서드·경로 | 설명 |
|---|---|
| `GET /analyze/<code>` | **통합 리포트** (재무·차트·뉴스·추천·목표가, 병렬·부분실패 허용) |
| `GET /analyze/<code>/financial` | 재무 분석 |
| `GET /analyze/<code>/chart` | 기술적 분석 |
| `GET /analyze/<code>/news` | 뉴스 분석 |
| `GET /analyze/<code>/recommendation` | 종합 추천 |
| `GET /analyze/<code>/price-target?expected_return=&max_loss=` | 목표가·손절 |
| `GET /search?q=<keyword>` | 종목 검색(자동완성, 상위 5개) |
| `GET /api/stock/kr/<code>` | 국내 시세 |
| `GET /api/stock/kr/<code>/price-history?period=` | 기간별 시세(차트용) |
| `GET /api/stock/us/<symbol>` | 해외 시세 |
| `GET /api/quote/<code>` | 종목 현재가 |
| `GET /api/indices` | 시장 지수 |
| `GET /api/health` | DB/서버 상태 |

---

## 5. 기술 스택 (실제 채택)

| 항목 | 채택 | 비고 |
|---|---|---|
| **백엔드** | **Flask** (Python 3.9+) | `main.py` / `run_server.py`, 포트 8000 |
| **데이터 수집** | **PYKRX**(국내), **yfinance**(해외) | 크롤링 대신 라이브러리. 국내 재무는 KRX 로그인(`.env`) |
| **뉴스 수집** | 네이버 + 구글 뉴스 + yfinance | requests/BeautifulSoup 기반 크롤링 |
| **분석/지표** | pandas 기반 계산 | RSI·MACD·볼린저 등 룰 기반 |
| **저장소** | **SQLite** | 종목별 분석 결과 일 단위 캐시 |
| **프론트엔드** | **Vue 3 (Vite)** SPA, Chart.js | `frontend/`, 빌드 산출물을 Flask가 정적 서빙 |
| **환경** | 로컬 (Mac/Windows) | 개발 서버: Vite `:5173`, 통합: Flask `:8000` |

### 코드 구조
```
src/
  collectors/   krx_collector · yfinance_collector · news_collector · index_collector
  analyzers/    financial · chart · news · recommendation_engine · price_target_calculator
  storage/      data_store (SQLite)
  api/          routes (Flask blueprint)
frontend/src/
  components/   추천·목표가·재무·차트·뉴스·검색·관심종목·홈·시장지수 등
  composables/  useStock · useCurrentStock · useWatchlist · useAsyncData
  api/          client.js
```

---

## 6. 성공 기준 달성 현황

**필수 (계획 PRD 기준)**
- ✅ 종목 입력 → 재무 지표 + 차트 지표 계산·표시
- ✅ 뉴스 수집 + 룰 점수 → 종합 추천(Buy/Hold/Sell)
- ✅ 종목별 목표가·손절 라인 자동 제안
- ✅ 종합 리포트가 대시보드에 표시
- ✅ 통합 API(`/analyze/<code>`) 단일 호출로 전체 리포트

**우수 (가점) — 달성**
- ✅ 다중 종목 검색·전환 (#009)
- ✅ 차트 시각화 고도화 — 기간 선택 + 이동평균·볼린저 오버레이 + 등락률·OHLC (#011)
- ✅ 관심 종목·홈 화면·업종별 재무 평균·시장 지수 (#010 외)
- ✅ 모바일-퍼스트 반응형 디자인

---

## 7. 범위 밖 / 미구현 (V2 이후)

- ❌ **자동매매 (주문·체결, 증권사 API 연동)** — V2 핵심
- ❌ 실시간 시세 스트리밍 (V1은 과거/일별 데이터 기준)
- ❌ 머신러닝/감성분석 기반 추천 고도화 (V1은 키워드 룰)
- ❌ 포트폴리오 최적화, 마진/옵션
- ❌ 모바일 앱 (웹 기반만)
- ❌ 실시간 알림 (Slack/Email)
- ❌ 클라우드 배포

---

## 8. 알려진 제약 / 리스크

| 항목 | 내용 | 현재 대응 |
|---|---|---|
| KRX 로그인 의존 | 국내 재무 지표는 `.env`의 `KRX_ID/PW` 필요 | 자격 미설정 시 부채비율 등은 yfinance 폴백 (ADR 0005) |
| 뉴스 소스 변경/차단 | 국내 뉴스는 크롤링 기반이라 구조 변경에 취약 | 멀티소스 + 중복 제거로 완화, 부분 실패 허용 설계 |
| 뉴스 점수 정확도 | 키워드 룰이라 뉘앙스 반영 한계 | V1 의도된 단순화 (동작 우선), 고도화는 V2 |
| 데이터 신선도 | 일별/과거 데이터 기준 (실시간 아님) | 일 단위 캐싱, `as_of` 표기 |

---

## 9. 실행 방법

```bash
# 백엔드 (http://localhost:8000, 빌드된 프론트엔드 정적 서빙)
./venv/bin/python run_server.py

# 프론트엔드 개발 서버 (http://localhost:5173, HMR)
cd frontend && npm run dev

# 프론트엔드 프로덕션 빌드 (frontend/dist → Flask 서빙)
cd frontend && npm run build
```

---

## 10. 향후 확장 (V2)

1. **자동매매 지원** (증권사 API 연동, 주문·체결) — V2 핵심
2. 실시간 시세 스트리밍
3. ML/감성분석 기반 추천 고도화
4. 포트폴리오 분석·최적화
5. 실시간 알림 (Slack/Email)
6. 클라우드 배포 / 모바일 앱

---

*참고 문서: 계획 PRD [`stock-analysis-system-prd.md`](./stock-analysis-system-prd.md) · 원본 스펙 [`spec.md`](../../spec.md) · 이슈별 구현 기록 [`IMPLEMENTATION/`](../../IMPLEMENTATION/) · 이슈 원본 [`.scratch/issues/`](../issues/)*
