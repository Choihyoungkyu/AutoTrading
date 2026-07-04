import pytest
from unittest.mock import patch
from src.analyzers.recommendation_engine import RecommendationEngine


@pytest.fixture
def engine():
    return RecommendationEngine()


# --- 등급 경계 (Buy > 0.65, Hold 0.35~0.65, Sell < 0.35) ---

def test_grade_buy(engine):
    result = engine.generate(0.8, 0.8, 0.8)
    assert result["grade"] == "buy"
    assert result["score"] == 0.8


def test_grade_hold(engine):
    result = engine.generate(0.5, 0.5, 0.5)
    assert result["grade"] == "hold"
    assert result["score"] == 0.5


def test_grade_sell(engine):
    result = engine.generate(0.1, 0.1, 0.1)
    assert result["grade"] == "sell"
    assert result["score"] == 0.1


def test_boundary_065_is_hold(engine):
    # 정확히 0.65는 Hold (Buy는 0.65 초과)
    assert engine.generate(0.65, 0.65, 0.65)["grade"] == "hold"


def test_boundary_just_above_065_is_buy(engine):
    assert engine.generate(0.66, 0.66, 0.66)["grade"] == "buy"


def test_boundary_035_is_hold(engine):
    assert engine.generate(0.35, 0.35, 0.35)["grade"] == "hold"


def test_boundary_just_below_035_is_sell(engine):
    assert engine.generate(0.34, 0.34, 0.34)["grade"] == "sell"


def test_weights_applied(engine):
    # 차트(40%)만 높을 때 가중 반영: 0*0.3 + 1*0.4 + 0*0.3 = 0.4
    result = engine.generate(0.0, 1.0, 0.0)
    assert result["score"] == 0.4
    assert result["grade"] == "hold"


def test_reasoning_present(engine):
    result = engine.generate(0.8, 0.7, 0.7)
    assert isinstance(result["reasoning"], str)
    assert "매수" in result["reasoning"]


# --- 정규화 ---

def test_normalize_financial():
    assert RecommendationEngine.normalize_financial({"verdict": "저평가"}) == 0.8
    assert RecommendationEngine.normalize_financial({"verdict": "고평가"}) == 0.2
    assert RecommendationEngine.normalize_financial({"verdict": "중립"}) == 0.5
    assert RecommendationEngine.normalize_financial(None) == 0.5


def test_normalize_chart():
    assert RecommendationEngine.normalize_chart({"signal": "buy", "confidence": 1.0}) == 1.0
    assert RecommendationEngine.normalize_chart({"signal": "sell", "confidence": 1.0}) == 0.0
    assert RecommendationEngine.normalize_chart({"signal": "hold", "confidence": 0.5}) == 0.5


def test_normalize_news():
    assert RecommendationEngine.normalize_news({"score": 1.0}) == 1.0
    assert RecommendationEngine.normalize_news({"score": -1.0}) == 0.0
    assert RecommendationEngine.normalize_news({"score": 0.0}) == 0.5


# --- 엔드포인트 ---

def test_recommendation_endpoint():
    from main import create_app
    client = create_app().test_client()

    with patch("src.api.routes.store.load_financial", return_value={"verdict": "저평가"}), \
         patch("src.api.routes.chart_analyzer.analyze", return_value={"signal": "buy", "confidence": 0.8}), \
         patch("src.api.routes.store.load_news", return_value={"score": 0.6}):
        resp = client.get("/analyze/005930/recommendation")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == "005930"
        assert data["grade"] in ("buy", "hold", "sell")
        assert "components" in data


def test_recommendation_endpoint_no_data():
    from main import create_app
    client = create_app().test_client()

    with patch("src.api.routes.store.load_financial", return_value=None), \
         patch("src.api.routes.financial_analyzer.analyze", return_value=None), \
         patch("src.api.routes.chart_analyzer.analyze", return_value=None), \
         patch("src.api.routes.store.load_news", return_value=None), \
         patch("src.api.routes.news_analyzer.analyze", return_value=None):
        resp = client.get("/analyze/005930/recommendation")
        assert resp.status_code == 404
