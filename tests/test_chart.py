import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.analyzers.chart_analyzer import ChartAnalyzer


@pytest.fixture
def mock_yf():
    yf = MagicMock()
    return yf


@pytest.fixture
def analyzer(mock_yf):
    return ChartAnalyzer(mock_yf)


@pytest.fixture
def fixed_ohlcv_df():
    """고정된 테스트용 OHLCV DataFrame (100행)"""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    close = np.linspace(60000, 75000, 100)  # 점진적 상승
    open_ = close - np.random.uniform(100, 500, 100)
    high = close + np.random.uniform(100, 500, 100)
    low = close - np.random.uniform(100, 500, 100)
    volume = np.random.uniform(1000000, 5000000, 100)

    df = pd.DataFrame({
        "date": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "symbol": ["005930.KS"] * 100,
    })
    df.set_index("date", inplace=True)
    return df


def test_signal_determination_buy():
    """신호 판단: RSI < 30 AND MA20 > MA50 → 'buy'"""
    analyzer = ChartAnalyzer()
    indicators = {
        "rsi": 25.0,
        "ma_20": 72000.0,
        "ma_50": 70000.0,
        "macd_line": 0,
        "macd_signal": 0,
        "macd_histogram": 0,
        "bb_upper": 0,
        "bb_middle": 0,
        "bb_lower": 0,
    }
    signal, confidence = analyzer._determine_signal(indicators)
    assert signal == "buy"
    assert 0 <= confidence <= 1


def test_signal_determination_sell():
    """신호 판단: RSI > 70 AND MA20 < MA50 → 'sell'"""
    analyzer = ChartAnalyzer()
    indicators = {
        "rsi": 75.0,
        "ma_20": 68000.0,
        "ma_50": 70000.0,
        "macd_line": 0,
        "macd_signal": 0,
        "macd_histogram": 0,
        "bb_upper": 0,
        "bb_middle": 0,
        "bb_lower": 0,
    }
    signal, confidence = analyzer._determine_signal(indicators)
    assert signal == "sell"
    assert 0 <= confidence <= 1


def test_signal_determination_hold():
    """신호 판단: 조건 미충족 → 'hold'"""
    analyzer = ChartAnalyzer()
    indicators = {
        "rsi": 50.0,
        "ma_20": 70000.0,
        "ma_50": 70000.0,
        "macd_line": 0,
        "macd_signal": 0,
        "macd_histogram": 0,
        "bb_upper": 0,
        "bb_middle": 0,
        "bb_lower": 0,
    }
    signal, confidence = analyzer._determine_signal(indicators)
    assert signal == "hold"
    assert confidence == 0.5


def test_analyze_response_keys(analyzer, mock_yf, fixed_ohlcv_df):
    """응답 구조와 필드 유효성 검증"""
    mock_yf.get_ohlcv.return_value = fixed_ohlcv_df

    result = analyzer.analyze("005930")

    # 필수 키 존재 확인
    assert "code" in result
    assert "ma_20" in result
    assert "ma_50" in result
    assert "rsi" in result
    assert "macd" in result
    assert "bollinger_band" in result
    assert "signal" in result
    assert "confidence" in result

    # MACD 서브 구조
    assert "line" in result["macd"]
    assert "signal" in result["macd"]
    assert "histogram" in result["macd"]

    # 볼린저밴드 서브 구조
    assert "upper" in result["bollinger_band"]
    assert "middle" in result["bollinger_band"]
    assert "lower" in result["bollinger_band"]

    # 값 범위 검증
    assert result["signal"] in ["buy", "sell", "hold"]
    assert 0 <= result["confidence"] <= 1


def test_analyze_no_data(analyzer, mock_yf):
    """데이터가 없는 경우 None 반환"""
    mock_yf.get_ohlcv.return_value = pd.DataFrame()

    result = analyzer.analyze("999999")

    assert result is None


def test_analyze_insufficient_data(analyzer, mock_yf):
    """데이터가 50행 미만인 경우 None 반환"""
    dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "open": np.random.uniform(60000, 70000, 30),
        "high": np.random.uniform(70000, 80000, 30),
        "low": np.random.uniform(50000, 60000, 30),
        "close": np.random.uniform(60000, 70000, 30),
        "volume": np.random.uniform(1000000, 5000000, 30),
    })
    df.set_index("date", inplace=True)

    mock_yf.get_ohlcv.return_value = df

    result = analyzer.analyze("005930")

    assert result is None


def test_chart_endpoint(mock_yf):
    """API 엔드포인트 테스트"""
    from main import create_app

    app = create_app()
    client = app.test_client()

    mock_response = {
        "code": "005930",
        "ma_20": 71234.56,
        "ma_50": 70123.45,
        "rsi": 25.5,
        "macd": {
            "line": 1000.5,
            "signal": 900.3,
            "histogram": 100.2,
        },
        "bollinger_band": {
            "upper": 75000.0,
            "middle": 70000.0,
            "lower": 65000.0,
        },
        "signal": "buy",
        "confidence": 0.75,
    }

    with patch("src.api.routes.chart_analyzer.analyze") as mock_analyze:
        mock_analyze.return_value = mock_response

        response = client.get("/analyze/005930/chart")

        assert response.status_code == 200
        data = response.get_json()
        assert data["code"] == "005930"
        assert data["signal"] == "buy"
        assert data["confidence"] == 0.75
