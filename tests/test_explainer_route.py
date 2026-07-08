from unittest.mock import patch, MagicMock


def _client():
    from main import create_app
    return create_app().test_client()


def test_explain_route_returns_statements_and_disclaimer():
    chart = {"rsi": 80, "macd": {"line": 1, "signal": 2}, "ma_20": 90, "ma_50": 100,
             "signal": "sell", "confidence": 0.9, "as_of": "20260708"}
    fin = {"pbr": 0.7, "per": 10, "debt_ratio": 250, "roe": -3, "dividend_yield": 2.0}
    with patch("src.api.routes.chart_analyzer") as ca, \
         patch("src.api.routes.financial_analyzer") as fa:
        ca.analyze.return_value = chart
        fa.get_financial_metrics.return_value = fin
        res = _client().get("/analyze/005930/explain")
    assert res.status_code == 200
    body = res.get_json()
    assert body["disclaimer"] == "현재 상태 설명이며 투자 권유가 아닙니다."
    assert body["code"] == "005930"
    # 예측 태그(sell/confidence)는 응답에 없어야 한다
    assert "signal" not in body and "confidence" not in body
    assert any(x["severity"] == "warning" for x in body["risks"])


def test_explain_route_404_when_no_chart_data():
    with patch("src.api.routes.chart_analyzer") as ca:
        ca.analyze.return_value = None
        res = _client().get("/analyze/000000/explain")
    assert res.status_code == 404
