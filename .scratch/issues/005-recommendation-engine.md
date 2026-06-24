# 종합 추천 엔진

## What to build

재무(평가), 차트(기술), 뉴스(심리) 세 관점의 점수를 합산하여 최종 Buy/Hold/Sell 추천 신호를 생성한다. 직장인이 "여러 관점을 균형있게 고려한 투자 결정"을 할 수 있게 한다.

**End-to-end 동작:**
```
POST /analyze/005930/recommendation
{
  "financial_score": 0.8,    // 저평가 → 높은 점수
  "chart_score": 0.6,        // 기술적 신호 (Buy)
  "news_score": 0.65         // 시장 심리 긍정적
}
→
{
  "grade": "buy",            // buy / hold / sell
  "score": 0.72,             // 최종 종합 점수 (0~1)
  "reasoning": "저평가 우량주 + 긍정적 뉴스 + 기술적 진입 신호"
}
```

## Acceptance criteria

- [ ] 재무 점수 정규화 (0~1)
- [ ] 차트 점수 정규화 (0~1)
- [ ] 뉴스 점수 정규화 (0~1)
- [ ] 가중 평균 계산 로직 (각 점수에 가중치 적용)
  - 기본: 재무 30% + 차트 40% + 뉴스 30%
- [ ] Buy/Hold/Sell 등급 결정 로직
  - Buy: 종합 점수 > 0.65
  - Hold: 0.35 ≤ 종합 점수 ≤ 0.65
  - Sell: 종합 점수 < 0.35
- [ ] `/analyze/005930/recommendation` 엔드포인트 구현
- [ ] 추천 사유 문장 생성 (왜 이 등급인가)
- [ ] 고정 점수로 단위 테스트 작성 (buy/hold/sell 경계 검증)

## Blocked by

- 002: 삼성전자 재무 분석 엔드포인트
- 003: 삼성전자 기술적 분석 & Buy/Sell 신호 생성
- 004: 삼성전자 뉴스 분석

## User Stories

- 7: 재무 점수 + 차트 점수 + 뉴스 점수가 합산된 종합 추천 등급 보기
