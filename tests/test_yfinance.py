import pytest
from src.collectors.yfinance_collector import YFinanceCollector


def _yfinance_available() -> bool:
    # yfinance 라이브 데이터 접근 가능 여부를 1회 프로브. 접근 불가 환경
    # (네트워크 차단·yfinance 응답 실패)에서는 아래 라이브 테스트를 skip한다.
    try:
        return not YFinanceCollector().get_ohlcv("AAPL", period="5d").empty
    except Exception:
        return False


requires_yfinance = pytest.mark.skipif(
    not _yfinance_available(),
    reason="yfinance 라이브 데이터 사용 불가 환경 (국내 경로는 pykrx/네이버로 전환됨)",
)


@requires_yfinance
def test_yfinance_aapl():
    collector = YFinanceCollector()
    df = collector.get_ohlcv("AAPL", period="1mo")
    assert not df.empty


@requires_yfinance
def test_yfinance_tsla():
    collector = YFinanceCollector()
    df = collector.get_ohlcv("TSLA", period="1mo")
    assert not df.empty


@requires_yfinance
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
