# 구현 기록: 이슈 003 — 삼성전자 기술적 분석 & Buy/Sell 신호

## 개요

yfinance로 삼성전자 1년치 OHLCV 데이터를 수집하고, `ta` 라이브러리로 기술적 지표를 계산한 뒤 매수/매도/중립 신호를 판단하는 API를 구현했다.

- **완료 커밋**: `0883229` (feat: 이슈 003 삼성전자 기술적 분석 차트 API 구현)
- **대시보드 반영 커밋**: `f035a9d` (feat: 웹 대시보드에 차트 분석 섹션 추가)

---

## 구현 파일

| 파일 | 역할 |
|---|---|
| `src/analyzers/chart_analyzer.py` | 기술적 지표 계산 및 신호 판단 |
| `src/api/routes.py` → `analyze_chart()` | API 엔드포인트 |
| `tests/test_chart.py` | 단위 테스트 (mock 기반) |

---

## API

```
GET /analyze/{code}/chart
```

**응답 예시:**
```json
{
  "code": "005930",
  "ma_20": 70234.56,
  "ma_50": 72100.00,
  "rsi": 28.5,
  "macd": {
    "line": 500.12,
    "signal": 450.33,
    "histogram": 49.79
  },
  "bollinger_band": {
    "upper": 75000.0,
    "middle": 70000.0,
    "lower": 65000.0
  },
  "signal": "buy",
  "confidence": 0.75
}
```

---

## 핵심 로직

### 데이터 수집
- yfinance로 `{code}.KS` 심볼 1년치 OHLCV 수집
- 데이터 50행 미만이면 `None` 반환 (지표 계산 불가)

### 지표 계산 (`_calculate_indicators`)

| 지표 | 방법 |
|---|---|
| MA20, MA50 | `pandas.rolling().mean()` |
| RSI (14주기) | `ta.momentum.RSIIndicator` |
| MACD | `ta.trend.MACD` (line / signal / histogram) |
| 볼린저밴드 | `ta.volatility.BollingerBands` (20주기, 2σ) |

### 신호 판단 (`_determine_signal`)

| 신호 | 조건 | 신뢰도 |
|---|---|---|
| `buy` | RSI < 30 AND MA20 > MA50 | 과매도 폭 + MA 괴리율 평균 |
| `sell` | RSI > 70 AND MA20 < MA50 | 과매수 폭 + MA 괴리율 평균 |
| `hold` | 그 외 | 0.5 고정 |

---

## 테스트

```bash
pytest tests/test_chart.py -v
```

**커버된 케이스:**
- `test_signal_determination_buy` — RSI 25, MA20 > MA50 → `buy`
- `test_signal_determination_sell` — RSI 75, MA20 < MA50 → `sell`
- `test_signal_determination_hold` — RSI 50 → `hold`
- `test_analyze_response_keys` — 응답 구조 전체 키 검증 (mock OHLCV 100행)
- `test_analyze_no_data` — 빈 DataFrame → `None`
- `test_analyze_insufficient_data` — 30행 → `None`
- `test_chart_endpoint` — Flask 테스트 클라이언트로 엔드포인트 200 응답 확인

---

## 이슈 원본

`.scratch/issues/003-samsung-chart.md`
