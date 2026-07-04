# 구현 기록: 이슈 004 — 뉴스 분석 (시장 심리)

## 개요

여러 소스에서 종목 뉴스를 모아 최근 5일·중복 제거 후 키워드 룰 기반 감정 점수를 매기는 API와 대시보드 카드를 구현했다. 이슈 원문은 yfinance 뉴스 API를 명시했으나 국내 종목 조회가 불가해 소스를 다변화했다(→ ADR 0006).

- **백엔드 커밋**: `d26bc02` (feat: 뉴스 분석 백엔드 및 기술적 분석 PYKRX 전환)
- **프론트 커밋**: `0cff18a` (feat: 뉴스 게시글·팝업 UI 및 화면 탭 레이아웃 전환)
- **결정 기록**: `docs/adr/0006-뉴스-수집-소스-다변화.md`

---

## 구현 파일

| 파일 | 역할 |
|---|---|
| `src/collectors/news_collector.py` | 멀티소스 수집·정규화·5일 필터·중복 제거 |
| `src/analyzers/news_analyzer.py` | 키워드 룰 감정 점수 |
| `src/storage/data_store.py` → `save_news`/`load_news` | 종목별 뉴스 캐시(news_cache) |
| `src/api/routes.py` → `analyze_news()` | API 엔드포인트 (cache-first) |
| `frontend/src/components/NewsAnalysis.vue` | 게시글 목록 + 요약 팝업 카드 |
| `tests/test_news.py` | 감정·필터·중복·엔드포인트 테스트 |

---

## API

```
GET /analyze/{code}/news
```

**응답 예시:**
```json
{
  "code": "005930",
  "as_of": "2026-07-04",
  "score": 0.15,
  "sentiment": "positive",
  "article_count": 15,
  "source": "live",
  "headlines": [
    { "title": "삼성전자 영업이익 사상 최대", "score": 0.5,
      "url": "https://...", "source": "서울경제",
      "summary": "...", "date": "2026-07-04" }
  ]
}
```

> `source`는 `live`(실시간 수집 성공) 또는 `cache`(실패 시 최근 캐시 폴백).

---

## 핵심 로직

### 소스 (종목 유형별)
| 구분 | 소스 |
|---|---|
| 국내(6자리 숫자) | 네이버 모바일 뉴스 API + Google News RSS(종목명) |
| 해외(티커) | yfinance `Ticker.news` + Google News RSS(심볼) |

- Google RSS는 stdlib `xml.etree.ElementTree`로 파싱(신규 의존성 없음).
- 각 소스는 개별 try/except로 감싸 부분 실패 허용.

### 후처리 (순수 함수 — 네트워크 없이 테스트)
- `_within_days(items, days, now=None)`: 최근 N일 필터.
- `_dedupe(items)`: 제목 토큰 집합 **Jaccard 유사도 ≥ 0.6**이면 중복으로 보고 먼저 등장한 것만 유지(원본 매체 > 구글 순으로 우선).

### 감정 (키워드 룰, PRD V1)
- positive/negative 사전으로 헤드라인별 `+0.5·pos − 0.5·neg`를 `[-1,1]` clamp.
- 전체 `score`=평균 → `>0.15 positive / <-0.15 negative / else neutral`.

---

## 테스트

```bash
pytest tests/test_news.py -v
```
- 감정 positive/negative/neutral, 빈 결과 → `None`
- `_within_days` 고정 now로 5일 밖 제외, `_dedupe` 유사 제목 1건만
- 엔드포인트 200 + 구조, 캐시 폴백(`source=="cache"`)

---

## 이슈 원본

`.scratch/issues/004-samsung-news.md`
