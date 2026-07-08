import pandas as pd
import pytest
from unittest.mock import patch
from contextlib import ExitStack


@pytest.fixture
def client():
    from main import create_app
    return create_app().test_client()


def _ohlcv():
    return pd.DataFrame({"date": ["2026-07-03"], "close": [70000]})


def _patches(**overrides):
    # 통합 엔드포인트가 호출하는 모든 의존성의 기본 mock. overrides로 개별 교체.
    defaults = {
        "src.api.routes.krx.get_ohlcv": _ohlcv(),
        "src.api.routes.krx.get_name": "삼성전자",
        "src.api.routes.store.load_financial": {"verdict": "저평가", "as_of": "2026-07-03"},
        "src.api.routes.store.load_news": {"score": 0.6, "sentiment": "positive"},
        "src.api.routes.chart_analyzer.analyze": {"signal": "buy", "confidence": 0.8},
        "src.api.routes.krx.get_consensus_target": None,
        "src.api.routes.store.save_financial": None,
        "src.api.routes.store.save_news": None,
    }
    defaults.update(overrides)
    stack = ExitStack()
    for target, value in defaults.items():
        stack.enter_context(patch(target, return_value=value))
    return stack


def test_integrated_normal(client):
    with _patches():
        resp = client.get("/analyze/005930")
        assert resp.status_code == 200
        data = resp.get_json()
        for key in ("stock_code", "stock_name", "current_price", "financial",
                    "chart", "news", "recommendation", "price_target", "timestamp"):
            assert key in data
        assert data["stock_code"] == "005930"
        assert data["stock_name"] == "삼성전자"
        assert data["current_price"] == 70000
        assert data["recommendation"]["grade"] in ("buy", "hold", "sell")
        assert data["price_target"]["target_price"] == 80500


def test_integrated_invalid_code(client):
    with _patches(**{"src.api.routes.krx.get_ohlcv": pd.DataFrame()}):
        resp = client.get("/analyze/999999")
        assert resp.status_code == 404


def test_integrated_partial_failure(client):
    # 차트 분석이 없어도(None) 나머지로 리포트를 구성한다.
    with _patches(**{"src.api.routes.chart_analyzer.analyze": None}):
        resp = client.get("/analyze/005930")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["chart"] is None
        assert data["financial"] is not None
        assert data["recommendation"]["grade"] in ("buy", "hold", "sell")
