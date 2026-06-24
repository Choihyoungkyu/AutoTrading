# 삼성전자 기술적 분석 & Buy/Sell 신호 생성

## What to build

yfinance에서 삼성전자의 과거 OHLCV 데이터를 받아 기술적 지표를 계산하고, 현재 차트가 보내는 신호를 판단한다. 직장인이 "지금 이 종목을 사야 하나?"에 대해 차트로 답할 수 있게 한다.

**End-to-end 동작:**
```
GET /analyze/005930/chart
→
{
  "ma_20": 70000,
  "ma_50": 72000,
  "rsi": 35,
  "macd": { "line": 500, "signal": 450, "histogram": 50 },
  "bollinger_band": { "upper": 75000, "middle": 70000, "lower": 65000 },
  "signal": "buy",  // 과매도(RSI<30) + MA 골든크로스
  "confidence": 0.75
}
```

## Acceptance criteria

- [ ] yfinance에서 삼성전자 과거 1년 OHLCV 데이터 수집
- [ ] ta 라이브러리로 MA(20, 50, 200), RSI, MACD, 볼린저밴드 계산
- [ ] Buy/Sell/Hold 신호 생성 로직 구현 (규칙 기반)
  - Buy: RSI < 30 (과매도) + 20MA > 50MA (상승세)
  - Sell: RSI > 70 (과매수) + 20MA < 50MA (하강세)
  - Hold: 그 외
- [ ] `/analyze/005930/chart` 엔드포인트 구현
- [ ] 신호의 신뢰도(confidence) 점수 추가
- [ ] 고정 OHLCV 데이터로 단위 테스트 작성 (mock)

## Blocked by

- 001: 프로젝트 초기화 & 데이터 수집 기본 구조

## User Stories

- 4: 과거 OHLCV 데이터 기반 기술적 지표(MA, RSI, MACD) 계산
- 5: 기술적 지표들이 현재 매수/매도/관망 신호 제시
