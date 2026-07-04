# 주식 분석 시스템 (Stock Analysis System)

종목 코드 하나로 **재무·차트·뉴스**를 자동 분석하고 **객관적 매수/매도 신호**를 제시하는 웹 대시보드.
"정보의 양이 아니라 빠른 판단과 감정 제거"라는 관점 아래, 개인 투자자가 5분 안에 판단을 내리도록 돕는다.

- 백엔드: **Flask** + PYKRX / 네이버 금융 / Google News / yfinance
- 프론트엔드: **Vue 3 (Vite)** SPA, Chart.js
- 저장: **SQLite** (종목별 분석 캐시)

---

## 주요 기능

| 이슈 | 기능 | 설명 |
|---|---|---|
| 001 | 데이터 수집·저장 | PYKRX 시세 + SQLite 저장, Flask API 골격 |
| 002 | 재무 분석 | PER·PBR·ROE·부채비율·배당 + 업계(반도체) 중앙값 비교 → 저평가/고평가 판정 |
| 003 | 기술적 분석 | MA·RSI·MACD·볼린저밴드 → Buy/Hold/Sell 신호 (PYKRX 기반) |
| 004 | 뉴스 분석 | 네이버+구글+yfinance 멀티소스, 최근 5일·중복 제거, 키워드 감정 점수 |
| 005 | 종합 추천 | 재무·차트·뉴스 가중 합산(30/40/30%) → Buy/Hold/Sell + 사유 |
| 006 | 목표가·손절 | 현재가 기반 목표가·손절가·리스크리워드 비율 (수익률/손실률 조절) |
| 007 | 통합 리포트 API | `/analyze/<code>` 한 번에 전체 통합 (병렬·캐시·부분 실패 허용) |
| 009 | 다중 종목 | 종목 검색(자동완성) + 어떤 국내 종목이든 대시보드 전환 |
| 011 | 주가 차트 | 일/주/달/년 기간 선택 + 이동평균·볼린저밴드 오버레이 |

대시보드는 항목별 **탭**(종합 추천 · 목표가·손절 · 개요 · 주가 차트 · 재무 · 기술적 분석 · 뉴스)으로 구성된다.

---

## API 엔드포인트

| 메서드·경로 | 설명 |
|---|---|
| `GET /analyze/<code>` | **통합 리포트** (재무·차트·뉴스·추천·목표가) |
| `GET /analyze/<code>/financial` | 재무 분석 |
| `GET /analyze/<code>/chart` | 기술적 분석 |
| `GET /analyze/<code>/news` | 뉴스 분석 |
| `GET /analyze/<code>/recommendation` | 종합 추천 |
| `GET /analyze/<code>/price-target?expected_return=&max_loss=` | 목표가·손절 |
| `GET /search?q=<keyword>` | 종목 검색(자동완성, 상위 5개) |
| `GET /api/stock/kr/<code>` | 국내 시세 |
| `GET /api/stock/kr/<code>/price-history?period=` | 기간별 시세(차트용) |
| `GET /api/health` | DB 상태 |

응답 예시는 `IMPLEMENTATION/` 각 문서를 참고.

---

## 실행 방법

### 1) 백엔드

```bash
# 가상환경 + 의존성
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 재무 지표(KRX 로그인) 자격증명 — 저장소 루트 .env (커밋 제외)
#   KRX_ID=...
#   KRX_PW=...

# 서버 실행 (http://localhost:8000)
./venv/bin/python run_server.py
```

### 2) 프론트엔드 (빌드 산출물을 Flask가 서빙)

```bash
cd frontend
npm install
npm run build      # frontend/dist 생성 → Flask가 정적 서빙
```

빌드 후 `http://localhost:8000` 에서 대시보드 확인. (개발 시 `npm run dev` + Vite 프록시)

---

## 프로젝트 구조

```
├── main.py / run_server.py     # Flask 앱 · 실행 스크립트
├── src/
│   ├── collectors/             # krx_collector, yfinance_collector, news_collector
│   ├── analyzers/              # financial, chart, news, recommendation, price_target
│   ├── storage/                # data_store (SQLite, 종목별 캐시)
│   └── api/routes.py           # 모든 엔드포인트
├── frontend/src/
│   ├── components/             # 카드·헤더·탭 컴포넌트
│   ├── composables/            # useCurrentStock, useStock, useAsyncData
│   └── api/client.js           # 백엔드 호출 래퍼
├── tests/                      # pytest (분석기·엔드포인트·통합)
├── IMPLEMENTATION/             # 이슈별 구현 기록
├── docs/adr/                   # 아키텍처 결정 기록(ADR)
└── .scratch/                   # PRD · 이슈 트래커
```

---

## 테스트

```bash
./venv/bin/python -m pytest -q
```

- 분석 로직은 mock 기반 단위 테스트 (네트워크 불필요, 결정적).
- 통합(E2E)은 정상/잘못된 종목/부분 실패 케이스 검증.
- yfinance 라이브 시세 테스트는 접근 불가 환경에서 자동 skip.

---

## 데이터 소스 · 제약

- **국내 시세**: PYKRX. **재무**: 네이버 금융. **뉴스**: 네이버 모바일 API + Google News RSS(+해외 yfinance).
- 소스 전환 경위는 `docs/adr/` 참고 (재무 0004→0005, 뉴스 0006).
- **해외 종목**: 뉴스는 지원하나, 현재가·재무·차트가 PYKRX/이 환경의 yfinance 제약으로 end-to-end 미지원(국내 종목 중심).

---

## 문서

- 이슈별 구현 기록: [`IMPLEMENTATION/`](./IMPLEMENTATION/README.md)
- 아키텍처 결정: [`docs/adr/`](./docs/adr/)
- 기획/네러티브: [`.scratch/prd/stock-analysis-system-prd.md`](./.scratch/prd/stock-analysis-system-prd.md)
