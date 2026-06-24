import pytest
from src.collectors.yfinance_collector import YFinanceCollector


def test_yfinance_aapl():
    collector = YFinanceCollector()
    df = collector.get_ohlcv("AAPL", period="1mo")
    assert not df.empty


def test_yfinance_tsla():
    collector = YFinanceCollector()
    df = collector.get_ohlcv("TSLA", period="1mo")
    assert not df.empty


def test_yfinance_columns():
    collector = YFinanceCollector()
    df = collector.get_ohlcv("AAPL")
    expected = {"date", "open", "high", "low", "close", "volume", "symbol"}
    assert expected.issubset(set(df.columns))


def test_invalid_symbol_raises():
    collector = YFinanceCollector()
    with pytest.raises(ValueError):
        collector.get_ohlcv("INVALID_TICKER_XYZ999")


def test_yfinance_info():
    collector = YFinanceCollector()
    info = collector.get_info("AAPL")
    assert isinstance(info, dict)


def test_yfinance_news():
    collector = YFinanceCollector()
    news = collector.get_news("AAPL")
    assert isinstance(news, list)
