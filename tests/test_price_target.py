import pandas as pd
import pytest
from unittest.mock import patch
from src.analyzers.price_target_calculator import PriceTargetCalculator


@pytest.fixture
def calc():
    return PriceTargetCalculator()


def test_suggest_basic(calc):
    # 이슈 006 예시: 70000, 15%, 10%
    r = calc.suggest(70000, 0.15, 0.10)
    assert r["target_price"] == 80500
    assert r["stop_loss"] == 63000
    assert r["risk_reward_ratio"] == 1.5


def test_suggest_defaults(calc):
    r = calc.suggest(100000)
    assert r["expected_return"] == 0.15
    assert r["max_loss"] == 0.10
    assert r["target_price"] == 115000
    assert r["stop_loss"] == 90000


def test_risk_reward_ratio(calc):
    # 기대 20% / 손실 10% → RR 2.0
    r = calc.suggest(50000, 0.20, 0.10)
    assert r["risk_reward_ratio"] == 2.0


def test_suggest_consensus_override(calc):
    # 증권사 컨센서스 목표가 주입 → 그 값을 목표가로, 기대수익률은 역산
    r = calc.suggest(70000, target_price=90000)
    assert r["target_price"] == 90000
    assert r["source"] == "consensus"
    assert r["expected_return"] == round((90000 - 70000) / 70000, 4)
    assert r["stop_loss"] == 63000  # 손절은 컨센서스와 무관한 가드레일(−10%)


def test_endpoint_estimate_fallback():
    # 컨센서스 없는 종목 → 기대수익률 기반 추정으로 폴백
    from main import create_app
    client = create_app().test_client()

    df = pd.DataFrame({"date": ["2026-07-03"], "close": [70000]})
    with patch("src.api.routes.krx.get_ohlcv", return_value=df), \
         patch("src.api.routes.krx.get_consensus_target", return_value=None):
        resp = client.get("/analyze/005930/price-target?expected_return=0.15&max_loss=0.10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["current_price"] == 70000
        assert data["target_price"] == 80500
        assert data["stop_loss"] == 63000
        assert data["source"] == "estimate"
        assert data["consensus"] is None
        assert data["code"] == "005930"


def test_endpoint_consensus():
    # 컨센서스 있는 종목 → 목표가는 컨센서스 평균, source=consensus
    from main import create_app
    client = create_app().test_client()

    df = pd.DataFrame({"date": ["2026-07-03"], "close": [70000]})
    consensus = {"target_price": 90000, "recomm_mean": 4.1, "as_of": "2026-07-07"}
    with patch("src.api.routes.krx.get_ohlcv", return_value=df), \
         patch("src.api.routes.krx.get_consensus_target", return_value=consensus):
        resp = client.get("/analyze/005930/price-target")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["target_price"] == 90000
        assert data["source"] == "consensus"
        assert data["consensus"]["recomm_mean"] == 4.1


def test_endpoint_no_data():
    from main import create_app
    client = create_app().test_client()

    with patch("src.api.routes.krx.get_ohlcv", return_value=pd.DataFrame()):
        resp = client.get("/analyze/005930/price-target")
        assert resp.status_code == 404
