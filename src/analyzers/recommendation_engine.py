# 재무(평가) + 차트(기술) + 뉴스(심리) 세 관점을 가중 합산해
# 최종 Buy/Hold/Sell 신호를 만든다.
WEIGHTS = {"financial": 0.3, "chart": 0.4, "news": 0.3}

BUY_THRESHOLD = 0.65
SELL_THRESHOLD = 0.35


class RecommendationEngine:
    def generate(self, financial_score: float, chart_score: float,
                 news_score: float) -> dict:
        """정규화된 세 점수(0~1)를 가중 평균해 등급·사유를 만든다."""
        score = (
            financial_score * WEIGHTS["financial"]
            + chart_score * WEIGHTS["chart"]
            + news_score * WEIGHTS["news"]
        )
        score = round(score, 2)

        if score > BUY_THRESHOLD:
            grade = "buy"
        elif score >= SELL_THRESHOLD:
            grade = "hold"
        else:
            grade = "sell"

        return {
            "grade": grade,
            "score": score,
            "reasoning": self._reasoning(grade, financial_score, chart_score, news_score),
            "components": {
                "financial": round(financial_score, 2),
                "chart": round(chart_score, 2),
                "news": round(news_score, 2),
            },
            "weights": WEIGHTS,
        }

    def _reasoning(self, grade, fs, cs, ns) -> str:
        fin = "저평가" if fs >= 0.65 else "고평가" if fs < 0.35 else "적정가"
        chart = "기술적 매수 신호" if cs >= 0.6 else "기술적 매도 신호" if cs < 0.4 else "기술적 중립"
        news = "긍정적 뉴스 심리" if ns >= 0.6 else "부정적 뉴스 심리" if ns < 0.4 else "중립적 뉴스 심리"
        grade_txt = {"buy": "매수 추천", "hold": "관망", "sell": "매도 고려"}[grade]
        return f"{fin} · {chart} · {news} → 종합 {grade_txt}"

    # --- 각 분석기 출력을 0~1 점수로 정규화 (재사용·테스트 대상) ---

    @staticmethod
    def normalize_financial(result: dict) -> float:
        # 재무 판정: 저평가일수록 높은 점수
        verdict = (result or {}).get("verdict")
        return {"저평가": 0.8, "고평가": 0.2}.get(verdict, 0.5)

    @staticmethod
    def normalize_chart(result: dict) -> float:
        # 차트 신호 + 신뢰도: buy는 0.5~1.0, sell은 0.0~0.5, hold는 0.5
        result = result or {}
        signal = result.get("signal", "hold")
        confidence = result.get("confidence", 0.5)
        if signal == "buy":
            return round(0.5 + 0.5 * confidence, 2)
        if signal == "sell":
            return round(0.5 - 0.5 * confidence, 2)
        return 0.5

    @staticmethod
    def normalize_news(result: dict) -> float:
        # 뉴스 감정 점수 [-1, 1] → [0, 1]
        raw = (result or {}).get("score", 0.0)
        return round((raw + 1) / 2, 2)
