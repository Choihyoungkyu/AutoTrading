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
    def technical_rating(score) -> dict:
        # 차트 지표 투표 점수(0~100)를 TradingView식 5단계 기술적 평가로 매핑.
        # (score-50)/50 = 지표 순매수 비율(-1~1). ±0.1/±0.5 임계값은 TradingView 방식과 동일.
        if score is None:
            return {"grade": "none", "label": "분석 불가"}
        v = (score - 50) / 50.0
        if v >= 0.5:
            return {"grade": "strong_buy", "label": "적극 매수"}
        if v >= 0.1:
            return {"grade": "buy", "label": "매수"}
        if v > -0.1:
            return {"grade": "neutral", "label": "중립"}
        if v > -0.5:
            return {"grade": "sell", "label": "매도"}
        return {"grade": "strong_sell", "label": "적극 매도"}

    @staticmethod
    def normalize_news(result: dict) -> float:
        # 뉴스 감정 점수 [-1, 1] → [0, 1]
        raw = (result or {}).get("score", 0.0)
        return round((raw + 1) / 2, 2)

    # --- 프론트 확장: confidence / factors / dimensions ---

    def extend(self, result: dict, financial: dict, chart: dict, news: dict,
               fs: float, cs: float, ns: float) -> dict:
        """기존 recommendation 결과에 confidence·factors·dimensions 추가.
        원본 분석 dict(financial/chart/news)와 정규화 점수(fs/cs/ns)를 재활용한다."""
        financial = financial or {}
        chart = chart or {}
        news = news or {}

        # factors: 5개 항목 0~100
        # 재무 건전성: debt_ratio(낮을수록↑) + roe(높을수록↑)
        debt = financial.get("debt_ratio")
        roe = financial.get("roe")
        health = 50
        if debt is not None:
            health = max(0, min(100, 100 - debt / 2))  # 부채 200%면 0점
        if roe is not None:
            health = round((health + max(0, min(100, roe * 5))) / 2)  # ROE 20%면 100
        health = max(0, min(100, round(health)))

        # 밸류에이션: verdict 기반
        valuation = {"저평가": 80, "고평가": 20}.get(financial.get("verdict"), 50)

        # 기술적: chart score(0~100) 우선, 없으면 정규화 점수
        technical = chart.get("score")
        if technical is None:
            technical = round(cs * 100)

        # 모멘텀: RSI + OBV 방향으로 근사 (없으면 기술점수로 폴백)
        rsi = chart.get("rsi")
        if rsi is not None:
            momentum = max(0, min(100, round(rsi)))  # RSI 자체를 모멘텀 강도로
        else:
            momentum = round(cs * 100)

        # 뉴스 감성: 정규화 점수(0~1)*100
        news_score = round(ns * 100)

        factors = [
            {"name": "재무 건전성", "score": health},
            {"name": "밸류에이션", "score": valuation},
            {"name": "기술적 분석", "score": max(0, min(100, round(technical)))},
            {"name": "모멘텀", "score": momentum},
            {"name": "뉴스 감성", "score": news_score},
        ]

        # dimensions: 재무 / 기술적 / 뉴스 감성
        fin_signal = "buy" if fs >= 0.65 else "sell" if fs < 0.35 else "hold"
        fin_tag = "우수" if fs >= 0.65 else "주의" if fs < 0.35 else "보통"
        chart_signal = chart.get("signal", "hold")
        chart_tag = {"buy": "매수 우위", "sell": "매도 우위"}.get(chart_signal, "중립")
        news_sentiment = news.get("sentiment", "neutral")
        news_signal = {"positive": "buy", "negative": "sell"}.get(news_sentiment, "hold")
        news_tag = {"positive": "긍정", "negative": "부정"}.get(news_sentiment, "중립")

        dimensions = [
            {"name": "재무", "tag": fin_tag, "signal": fin_signal,
             "desc": f"{financial.get('verdict', '평가 정보 없음')}"},
            {"name": "기술적", "tag": chart_tag, "signal": chart_signal,
             "desc": f"기술 신호 {chart_signal}, 점수 {chart.get('score', '-')}"},
            {"name": "뉴스 감성", "tag": news_tag, "signal": news_signal,
             "desc": f"뉴스 심리 {news_tag} ({news.get('article_count', 0)}건)"},
        ]

        # confidence: 세 컴포넌트의 방향 일치도(모두 같은 방향이면↑) 기반 0~100
        scores = [fs, cs, ns]
        # 중립(0.5)에서 얼마나 벗어나 같은 방향인지: 평균 편차 크기
        avg = sum(scores) / len(scores)
        spread = sum(abs(s - avg) for s in scores) / len(scores)  # 낮을수록 일치
        strength = abs(avg - 0.5) * 2  # 방향 강도 0~1
        agreement = max(0.0, 1 - spread * 2)  # 일치도 0~1
        confidence = round((strength * 0.5 + agreement * 0.5) * 100)
        confidence = max(0, min(100, confidence))

        result["confidence"] = confidence
        result["factors"] = factors
        result["dimensions"] = dimensions
        return result
