from src.analyzers.stock_explainer import explain, DISCLAIMER


def test_rsi_oversold_is_info():
    r = explain({"rsi": 20}, {})
    rsi = [x for x in r["technical"] if x["label"] == "RSI"][0]
    assert "과매도" in rsi["statement"] and rsi["severity"] == "info"


def test_rsi_overbought_is_caution_and_in_risks():
    r = explain({"rsi": 80}, {})
    rsi = [x for x in r["technical"] if x["label"] == "RSI"][0]
    assert "과매수" in rsi["statement"] and rsi["severity"] == "caution"
    assert any(x["label"] == "RSI" for x in r["risks"])


def test_macd_and_ma_arrangement():
    r = explain({"macd_line": 5, "macd_signal": 3, "ma_20": 100, "ma_50": 90}, {})
    labels = {x["label"]: x["statement"] for x in r["technical"]}
    assert "상승 모멘텀" in labels["MACD"]
    assert "정배열" in labels["이동평균"]


def test_high_debt_and_negative_roe_are_warnings():
    r = explain({}, {"debt_ratio": 250, "roe": -5})
    sev = {x["label"]: x["severity"] for x in r["financial"]}
    assert sev["부채비율"] == "warning" and sev["ROE"] == "warning"
    assert len(r["risks"]) == 2


def test_pbr_undervalued_boundary():
    assert any("저평가" in x["statement"] for x in explain({}, {"pbr": 0.7})["financial"])
    assert not any(x["label"] == "PBR" for x in explain({}, {"pbr": 1.0})["financial"])


def test_low_liquidity_warning_optional():
    r = explain({}, {}, liquidity={"trade_value": 500_000_000})
    assert any(x["label"] == "유동성" and x["severity"] == "warning" for x in r["technical"])


def test_missing_fields_are_skipped_and_disclaimer_present():
    r = explain({}, {})
    assert r["technical"] == [] and r["financial"] == []
    assert r["disclaimer"] == DISCLAIMER
