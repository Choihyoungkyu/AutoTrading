import pandas as pd
from unittest.mock import patch

from src.ml.universe import UniverseSelector


def _ohlcv_by_ticker():
    # 거래대금이 뒤섞인 합성 프레임(종목코드 인덱스 + "거래대금" 컬럼).
    return pd.DataFrame(
        {
            "시가": [100, 200, 300, 400, 500],
            "거래대금": [30, 50, 10, 40, 20],
        },
        index=["005930", "000660", "035420", "051910", "005380"],
    )


def test_top_n_거래대금_내림차순():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()) as m:
        result = UniverseSelector().get_universe("20220301", top_n=3)
    # 거래대금 50,40,30 순 → 000660, 051910, 005930
    assert result == ["000660", "051910", "005930"]
    m.assert_called_once_with("20220301", "KOSPI")


def test_top_n이_종목수보다_크면_전체_반환():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe("20220301", top_n=999)
    assert result == ["000660", "051910", "005930", "005380", "035420"]
    assert len(result) == 5


def test_반환은_6자리_str_코드():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe("20220301", top_n=2)
    assert all(isinstance(c, str) and len(c) == 6 and c.isdigit() for c in result)


def test_빈_프레임이면_빈_리스트():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=pd.DataFrame()):
        result = UniverseSelector().get_universe("20220301")
    assert result == []


def test_예외시_빈_리스트():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", side_effect=Exception("network")):
        result = UniverseSelector().get_universe("20220301")
    assert result == []
