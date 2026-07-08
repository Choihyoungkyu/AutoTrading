import pandas as pd
from unittest.mock import patch

from src.ml.universe import UniverseSelector


def _ohlcv_by_ticker():
    # 거래대금이 뒤섞인 합성 프레임(종목코드 인덱스 + "거래대금" 컬럼).
    # 거래대금: 60,50,40,30,20,10 → 내림차순 시 A,B,C,D,E,F 코드 순.
    return pd.DataFrame(
        {
            "시가": [100, 200, 300, 400, 500, 600],
            "거래대금": [30, 50, 10, 40, 20, 60],
        },
        index=["005930", "000660", "035420", "051910", "005380", "068270"],
    )


def _ranked_codes():
    # 거래대금 내림차순: 60(068270),50(000660),40(051910),30(005930),20(005380),10(035420)
    return ["068270", "000660", "051910", "005930", "005380", "035420"]


def test_밴드_구간만_반환():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe_band("20220301", start_rank=2, end_rank=4)
    # [2,4) → 3위,4위 (0-기반) = 051910, 005930
    assert result == ["051910", "005930"]


def test_정렬_올바름_전체밴드():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe_band("20220301", start_rank=0, end_rank=6)
    assert result == _ranked_codes()


def test_min_value_필터():
    # min_value=25 → 거래대금 20,10 제외. 밴드 [0,6) 안에서 필터 후 남는 것만.
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe_band(
            "20220301", start_rank=0, end_rank=6, min_value=25)
    # 거래대금 >= 25: 60,50,40,30 → 068270,000660,051910,005930
    assert result == ["068270", "000660", "051910", "005930"]


def test_min_value_필터는_밴드_슬라이스_전에_적용():
    # min_value로 저유동성 제외 후 [start,end) 밴드를 잘라야 한다.
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe_band(
            "20220301", start_rank=1, end_rank=3, min_value=25)
    # 필터 후 랭킹: 068270,000660,051910,005930 → [1,3) = 000660,051910
    assert result == ["000660", "051910"]


def test_반환은_6자리_str_코드():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe_band("20220301", start_rank=0, end_rank=3)
    assert all(isinstance(c, str) and len(c) == 6 and c.isdigit() for c in result)


def test_단일_as_of만_호출():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker",
               return_value=_ohlcv_by_ticker()) as m:
        UniverseSelector().get_universe_band("20220301", start_rank=0, end_rank=3, market="KOSDAQ")
    # as_of 외 데이터 미사용: 정확히 그 날짜·시장 한 번만 호출.
    m.assert_called_once_with("20220301", "KOSDAQ")


def test_빈_프레임이면_빈_리스트():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=pd.DataFrame()):
        result = UniverseSelector().get_universe_band("20220301", start_rank=0, end_rank=3)
    assert result == []


def test_예외시_빈_리스트():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", side_effect=Exception("network")):
        result = UniverseSelector().get_universe_band("20220301", start_rank=0, end_rank=3)
    assert result == []


def test_밴드가_종목수_초과하면_가능한만큼():
    with patch("src.ml.universe.stock.get_market_ohlcv_by_ticker", return_value=_ohlcv_by_ticker()):
        result = UniverseSelector().get_universe_band("20220301", start_rank=4, end_rank=99)
    # 6종목 중 [4,99) → 5위,6위 = 005380,035420
    assert result == ["005380", "035420"]
