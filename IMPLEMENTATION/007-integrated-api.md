# 구현 기록: 이슈 007 — 통합 분석 리포트 API (Primary Seam)

## 개요

재무·차트·뉴스·추천·목표가를 한 번의 호출로 통합하는 Primary Seam 엔드포인트를 구현했다. 종목 유효성 검증, 병렬 실행, 캐시 활용, 부분 실패 허용을 포함한다.

- **커밋**: `7643e7f` (feat: 통합 분석 리포트 API, Primary Seam)

---

## 구현 파일

| 파일 | 역할 |
|---|---|
| `src/api/routes.py` → `analyze_all()`, `_safe()` | 통합 엔드포인트 |
| `tests/test_integrated.py` | 정상/잘못된 종목/부분 실패 E2E |

---

## API

```
GET /analyze/{code}
```

**응답 구조:**
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "current_price": 309500,
  "as_of": "2026-07-03",
  "financial": { ... },
  "chart": { ... },
  "news": { ... },
  "recommendation": { ... },
  "price_target": { ... },
  "timestamp": "2026-07-04T02:32:24+00:00"
}
```

---

## 핵심 로직

- **유효성 검증**: OHLCV 1회 조회로 현재가·기준일 확보. 없으면 404.
- **병렬 실행**: 재무·차트·뉴스를 `ThreadPoolExecutor(max_workers=3)`로 동시 실행(재무·뉴스는 캐시 우선).
- **캐시**: 라이브 결과를 저장해 재호출 시 5초 목표에 기여(콜드 ~5s → 캐시 ~0.3s).
- **부분 실패 허용**: 실패 분석은 `null`, 추천은 중립(0.5)으로 진행 → 리포트는 항상 구성.
- 추천은 세 결과 정규화 후 `recommendation_engine.generate`, 목표가는 현재가 기반.

---

## 테스트

```bash
pytest tests/test_integrated.py -v
```
- 정상: 200 + 9개 키 전부, 추천 등급·목표가 검증
- 잘못된 종목(빈 OHLCV): 404
- 부분 실패(차트 None): 200 + `chart: null`, 나머지 유지

---

## 이슈 원본

`.scratch/issues/007-integrated-api.md`
