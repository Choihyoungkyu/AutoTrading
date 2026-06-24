import pytest
from src.collectors.krx_collector import KRXCollector

SAMSUNG = "005930"


def test_krx_ohlcv_returns_dataframe():
    collector = KRXCollector()
    df = collector.get_ohlcv(SAMSUNG)
    assert not df.empty, "삼성전자 시세 데이터가 비어 있습니다"


def test_krx_ohlcv_columns():
    collector = KRXCollector()
    df = collector.get_ohlcv(SAMSUNG)
    expected = {"date", "open", "high", "low", "close", "volume", "code"}
    assert expected.issubset(set(df.columns))


def test_krx_ohlcv_code_column():
    collector = KRXCollector()
    df = collector.get_ohlcv(SAMSUNG)
    assert (df["code"] == SAMSUNG).all()


def test_krx_market_cap():
    collector = KRXCollector()
    result = collector.get_market_cap(SAMSUNG)
    assert isinstance(result, dict)
    if result:
        assert "per" in result or "pbr" in result
