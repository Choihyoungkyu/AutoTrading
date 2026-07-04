# 구현 기록: 이슈 006 — 목표가 & 손절 라인 자동 제안

## 개요

현재가(PYKRX 최신 종가)를 기반으로 목표가·손절가와 리스크/리워드 비율을 계산하는 API와, 기대수익률·최대손실률을 조절하는 카드를 구현했다.

- **백엔드 커밋**: `917507b` (feat: 목표가·손절 라인 자동 제안 백엔드)
- **프론트 커밋**: `d2bbcdb` (feat: 목표가·손절 카드 UI 및 탭 추가)

---

## 구현 파일

| 파일 | 역할 |
|---|---|
| `src/analyzers/price_target_calculator.py` | 목표가·손절가·RR 계산 |
| `src/api/routes.py` → `analyze_price_target()` | 현재가 조회 + 계산 |
| `frontend/src/components/PriceTargetCard.vue` | 목표/손절/RR + 슬라이더 조절 |
| `tests/test_price_target.py` | 계산·엔드포인트 테스트 |

---

## API

```
GET /analyze/{code}/price-target?expected_return=0.15&max_loss=0.10
```

**응답 예시 (현재가 70000):**
```json
{
  "code": "005930",
  "as_of": "2026-07-03",
  "current_price": 70000,
  "expected_return": 0.15,
  "max_loss": 0.10,
  "target_price": 80500,
  "stop_loss": 63000,
  "risk_reward_ratio": 1.5
}
```

---

## 핵심 로직

- `target_price = 현재가 × (1 + expected_return)`
- `stop_loss = 현재가 × (1 − max_loss)`
- `risk_reward_ratio = (target − 현재가) / (현재가 − stop)` (하락폭 0이면 `null`)
- `expected_return`/`max_loss`는 쿼리로 조절, 기본 15%/10%.
- 현재가는 `krx.get_ohlcv(code)` 최신 종가. 데이터 없으면 404.

---

## 테스트

```bash
pytest tests/test_price_target.py -v
```
- 기본 계산(70000→80500/63000, RR 1.5), 기본값, RR 계산
- 엔드포인트 200 + 구조, 데이터 없음 404

---

## 이슈 원본

`.scratch/issues/006-price-target.md`
