# 구현 기록: 이슈 005 — 종합 추천 엔진

## 개요

재무(평가)·차트(기술)·뉴스(심리) 세 관점 점수를 가중 합산해 최종 Buy/Hold/Sell 신호와 사유를 만드는 엔진과 대시보드 카드를 구현했다.

- **백엔드 커밋**: `2cfe135` (feat: 종합 추천 엔진 백엔드)
- **프론트 커밋**: `28e0a94` (feat: 종합 추천 카드 UI 및 기본 탭 지정)

---

## 구현 파일

| 파일 | 역할 |
|---|---|
| `src/analyzers/recommendation_engine.py` | 정규화 + 가중평균 + 등급/사유 |
| `src/api/routes.py` → `analyze_recommendation()` | 재무·차트·뉴스 수집·정규화·종합 |
| `frontend/src/components/RecommendationAnalysis.vue` | 등급·점수·사유·가중치 막대 카드 |
| `tests/test_recommendation.py` | 경계값·정규화·엔드포인트 테스트 |

---

## API

```
GET /analyze/{code}/recommendation
```

**응답 예시:**
```json
{
  "code": "005930",
  "grade": "buy",
  "score": 0.72,
  "reasoning": "저평가 · 기술적 매수 신호 · 긍정적 뉴스 심리 → 종합 매수 추천",
  "components": { "financial": 0.8, "chart": 0.6, "news": 0.65 },
  "weights": { "financial": 0.3, "chart": 0.4, "news": 0.3 },
  "available": { "financial": true, "chart": true, "news": true }
}
```

> 이슈 예시는 `POST`+점수 body였으나, 대시보드 표시와 기존 GET 컨벤션에 맞춰 **자동 수집형 GET**으로 구현. 이슈가 지정한 점수 계약은 순수 함수 `generate()`로 두어 고정 점수 테스트로 검증.

---

## 핵심 로직

### 정규화 (각 분석기 출력 → 0~1)
| 입력 | 규칙 |
|---|---|
| 재무 `verdict` | 저평가 0.8 / 중립 0.5 / 고평가 0.2 |
| 차트 `signal`+`confidence` | buy `0.5+0.5·conf` / sell `0.5−0.5·conf` / hold 0.5 |
| 뉴스 `score`[-1,1] | `(score+1)/2` |

### 가중 합산 & 등급 (`generate`)
- `score = 재무·0.3 + 차트·0.4 + 뉴스·0.3`
- Buy `>0.65` / Hold `0.35~0.65` / Sell `<0.35`
- 누락된 분석은 중립(0.5)로 진행.

---

## 테스트

```bash
pytest tests/test_recommendation.py -v
```
- 등급 경계(0.65/0.35 포함·초과·미만), 가중치 반영
- 정규화 3종, 엔드포인트 200 + 구조, 데이터 없음 404

---

## 이슈 원본

`.scratch/issues/005-recommendation-engine.md`
