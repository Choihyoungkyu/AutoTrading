"""C1: 재무 피처의 인과적(as-of) 조인 테스트 — 미래참조 누수 방지.

특정 시점 t의 재무 피처는 t 이하 최근 공시값만 써야 한다(미래 공시가 과거 봉에
새면 절대 안 됨). merge_asof(backward)로 이 규칙을 강제하고, 첫 공시 이전은 NaN.
"""
import numpy as np
import pandas as pd

from src.ml.fundamentals import join_fundamentals_asof


def _ohlcv(dates):
    return pd.DataFrame({"date": dates, "close": [float(i) for i in range(len(dates))]})


def test_each_row_gets_latest_disclosure_on_or_before_its_date():
    ohlcv = _ohlcv(["20210105", "20210115", "20210205"])
    fundamentals = pd.DataFrame({
        "date": ["20210101", "20210201"],
        "fund_per": [10.0, 12.0],
    })
    out = join_fundamentals_asof(ohlcv, fundamentals)
    # 0105,0115 → 0101 공시(10.0); 0205 → 0201 공시(12.0)
    assert out["fund_per"].tolist() == [10.0, 10.0, 12.0]
    assert len(out) == len(ohlcv)


def test_future_disclosure_does_not_leak_into_earlier_rows():
    # 누수 회귀: 공시일(0201)의 값(99.0)이 그 이전 봉(0105/0115)에 나타나면 실패.
    ohlcv = _ohlcv(["20210105", "20210115", "20210201", "20210210"])
    fundamentals = pd.DataFrame({
        "date": ["20210101", "20210201"],
        "fund_per": [10.0, 99.0],
    })
    out = join_fundamentals_asof(ohlcv, fundamentals)
    assert out["fund_per"].tolist() == [10.0, 10.0, 99.0, 99.0]
    # 공시일 이전 두 봉은 절대 미래값(99.0)을 받지 않는다.
    assert 99.0 not in out["fund_per"].tolist()[:2]


def test_rows_before_first_disclosure_are_nan():
    ohlcv = _ohlcv(["20201220", "20201231", "20210105"])
    fundamentals = pd.DataFrame({
        "date": ["20210101"],
        "fund_per": [10.0],
    })
    out = join_fundamentals_asof(ohlcv, fundamentals)
    assert np.isnan(out["fund_per"].iloc[0])
    assert np.isnan(out["fund_per"].iloc[1])
    assert out["fund_per"].iloc[2] == 10.0
