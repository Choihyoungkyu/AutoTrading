from src.collectors.news_collector import NewsCollector

# V1: 키워드 룰 기반 감정 사전 (PRD 결정 — ML은 V2로 미룸)
POSITIVE_KEYWORDS = [
    "상승", "사상 최대", "최대", "호실적", "신제품", "흑자",
    "성장", "강세", "돌파", "수주", "개선", "급등",
]
NEGATIVE_KEYWORDS = [
    "하락", "적자", "부진", "차질", "약세", "급락",
    "우려", "리콜", "소송", "감소", "손실",
]


class NewsAnalyzer:
    def __init__(self, news_collector: NewsCollector = None):
        self.news = news_collector or NewsCollector()

    def analyze(self, code: str) -> dict:
        """종목 뉴스를 모아 키워드 룰 기반 시장 심리 점수를 매긴다."""
        items = self.news.get_news(code)
        if not items:
            return None

        headlines = []
        for it in items:
            headlines.append({
                "title": it["title"],
                "score": round(self._score_title(it["title"]), 2),
                "url": it["url"],
                "source": it["source"],
                "summary": it.get("summary", ""),
                "date": it["published"].strftime("%Y-%m-%d"),
            })

        avg = round(sum(h["score"] for h in headlines) / len(headlines), 2)
        sentiment = (
            "positive" if avg > 0.15 else "negative" if avg < -0.15 else "neutral"
        )
        as_of = max(it["published"] for it in items).strftime("%Y-%m-%d")

        return {
            "code": code,
            "as_of": as_of,
            "score": avg,
            "sentiment": sentiment,
            "article_count": len(headlines),
            "source": "live",
            "headlines": headlines,
        }

    @staticmethod
    def _score_title(title: str) -> float:
        pos = sum(1 for k in POSITIVE_KEYWORDS if k in title)
        neg = sum(1 for k in NEGATIVE_KEYWORDS if k in title)
        return max(-1.0, min(1.0, 0.5 * pos - 0.5 * neg))
