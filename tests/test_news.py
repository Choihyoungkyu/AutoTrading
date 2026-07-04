import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.collectors.news_collector import NewsCollector
from src.analyzers.news_analyzer import NewsAnalyzer


def _item(title, published):
    return {"title": title, "url": "http://x", "source": "테스트", "published": published}


@pytest.fixture
def mock_collector():
    return MagicMock()


@pytest.fixture
def analyzer(mock_collector):
    return NewsAnalyzer(mock_collector)


# --- NewsAnalyzer 키워드 감정 ---

def test_sentiment_positive(analyzer, mock_collector):
    mock_collector.get_news.return_value = [
        _item("삼성전자 영업이익 사상 최대, 주가 강세", datetime(2026, 7, 4)),
        _item("반도체 수주 급등하며 실적 개선", datetime(2026, 7, 3)),
    ]
    result = analyzer.analyze("005930")
    assert result["sentiment"] == "positive"
    assert result["score"] > 0.15
    assert result["source"] == "live"
    assert result["article_count"] == 2
    assert all(-1 <= h["score"] <= 1 for h in result["headlines"])


def test_sentiment_negative(analyzer, mock_collector):
    mock_collector.get_news.return_value = [
        _item("실적 부진에 주가 급락, 적자 우려", datetime(2026, 7, 4)),
        _item("공급 차질로 손실 확대", datetime(2026, 7, 3)),
    ]
    result = analyzer.analyze("005930")
    assert result["sentiment"] == "negative"
    assert result["score"] < -0.15


def test_sentiment_neutral(analyzer, mock_collector):
    mock_collector.get_news.return_value = [
        _item("삼성전자 신규 사옥 이전 발표", datetime(2026, 7, 4)),
    ]
    result = analyzer.analyze("005930")
    assert result["sentiment"] == "neutral"


def test_analyze_no_news_returns_none(analyzer, mock_collector):
    mock_collector.get_news.return_value = []
    assert analyzer.analyze("005930") is None


# --- NewsCollector 순수 헬퍼 ---

def test_within_days_filters_old():
    now = datetime(2026, 7, 4, 12, 0)
    items = [
        _item("오늘 뉴스", datetime(2026, 7, 4)),
        _item("3일 전 뉴스", datetime(2026, 7, 1)),
        _item("10일 전 뉴스", datetime(2026, 6, 24)),
    ]
    kept = NewsCollector._within_days(items, days=5, now=now)
    titles = [it["title"] for it in kept]
    assert "오늘 뉴스" in titles
    assert "3일 전 뉴스" in titles
    assert "10일 전 뉴스" not in titles


def test_dedupe_removes_similar_titles():
    items = [
        _item("삼성전자 영업이익 사상 최대 기록", datetime(2026, 7, 4)),
        _item("삼성전자 영업이익 사상 최대 기록했다", datetime(2026, 7, 4)),
        _item("SK하이닉스 D램 가격 인상", datetime(2026, 7, 3)),
    ]
    kept = NewsCollector._dedupe(items)
    assert len(kept) == 2
    assert kept[0]["title"] == "삼성전자 영업이익 사상 최대 기록"


# --- 엔드포인트 ---

def test_news_endpoint_live():
    from main import create_app
    client = create_app().test_client()

    mock_response = {
        "code": "005930",
        "as_of": "2026-07-04",
        "score": 0.5,
        "sentiment": "positive",
        "article_count": 2,
        "source": "live",
        "headlines": [{"title": "호실적", "score": 0.5, "url": "", "source": "네이버뉴스", "date": "2026-07-04"}],
    }
    with patch("src.api.routes.news_analyzer.analyze", return_value=mock_response):
        resp = client.get("/analyze/005930/news")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["sentiment"] == "positive"
        assert data["source"] == "live"


def test_news_endpoint_cache_fallback():
    from main import create_app
    client = create_app().test_client()

    cached = {"code": "005930", "sentiment": "neutral", "score": 0.0, "source": "live", "headlines": []}
    with patch("src.api.routes.news_analyzer.analyze", return_value=None), \
         patch("src.api.routes.store.load_news", return_value=cached):
        resp = client.get("/analyze/005930/news")
        assert resp.status_code == 200
        assert resp.get_json()["source"] == "cache"
