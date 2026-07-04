# 구현 기록: 이슈 009 — 다중 종목 지원

## 개요

삼성전자(005930) 고정이던 대시보드를 어떤 국내 종목이든 검색·전환할 수 있게 확장했다. 종목 검색 API와 헤더 검색창, 전역 반응형 종목 상태를 추가했다.

- **백엔드 커밋**: `1d80b0b` (feat: 종목 검색 API)
- **프론트 커밋**: `e53b2f0` (feat: 다중 종목 대시보드)

**범위**: 국내 종목 중심. 해외는 PYKRX 현재가/재무/차트 의존 + 이 환경의 yfinance 시세 제약으로 end-to-end 미지원(뉴스만 해외 가능).

---

## 구현 파일

| 파일 | 역할 |
|---|---|
| `src/collectors/krx_collector.py` → `search()` | 네이버 자동완성 종목 검색 |
| `src/api/routes.py` → `search()` | `GET /search` 엔드포인트 |
| `frontend/src/composables/useCurrentStock.js` | 전역 반응형 종목(code/name/setStock) |
| `frontend/src/components/AppHeader.vue` | 검색창(자동완성 드롭다운) |
| 각 카드 + `useStock.js` | `currentCode` watch로 재조회 |
| `tests/test_search.py` | 검색 라우트 테스트 |

---

## API

```
GET /search?q={keyword}
```

**응답 예시:**
```json
[
  { "code": "000660", "name": "SK하이닉스", "market": "코스피" },
  { "code": "035420", "name": "NAVER", "market": "코스피" }
]
```

빈 쿼리는 `[]`, 상위 5개 반환.

---

## 핵심 로직

### 검색 (백엔드)
- 네이버 자동완성 `https://ac.stock.naver.com/ac?q=<kw>&target=stock` → `[{code,name,market}]`.

### 반응형 전환 (프론트)
- `useCurrentStock`의 `currentCode`/`currentName` 모듈 싱글턴을 검색창이 `setStock`으로 갱신.
- 모든 카드가 `watch(currentCode, load)`로 재조회. `api.*`는 이미 `code` 파라미터 지원.
- keep-alive 유지 — 비활성 탭도 마운트 상태라 종목 변경 시 함께 갱신.
- 종목별 캐싱은 기존 `financial_cache`/`news_cache`(code 키)로 동작.

---

## 테스트

```bash
pytest tests/test_search.py -v
```
- 검색 결과 반환(코드/이름), 빈 쿼리 → `[]`
- 다중 종목 통합 확인(수동): `/analyze/{000660,035420,051910,035720,005380}` 모두 동일 구조 200

---

## 이슈 원본

`.scratch/issues/009-multi-stock.md`
