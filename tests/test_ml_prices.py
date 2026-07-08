"""D1: point-in-time 포워드 분할조정 테스트.

핵심 불변식 2가지:
  (1) 과거 봉은 미래 분할로 절대 바뀌지 않는다(미래참조 누수 방지).
  (2) 분할일의 가짜 가격 점프는 제거된다(라벨=돈 불변식 보호).
"""
import pandas as pd

from src.ml.prices import adjust_ohlcv, derive_splits
from src.ml.labels import make_returns


def _ohlcv(dates, closes, lows=None, volumes=None):
    """테스트용 최소 OHLCV. open/high는 close와 동일하게 채운다."""
    lows = lows if lows is not None else closes
    volumes = volumes if volumes is not None else [1000] * len(dates)
    return pd.DataFrame({
        "date": dates,
        "open": closes,
        "high": closes,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


def test_no_splits_returns_prices_unchanged():
    df = _ohlcv(["20210101", "20210102", "20210103"], [100.0, 101.0, 102.0])
    out = adjust_ohlcv(df, splits=[])
    assert out["close"].tolist() == [100.0, 101.0, 102.0]
    assert out["volume"].tolist() == [1000, 1000, 1000]


def test_forward_split_removes_price_jump():
    # 20210103에 2:1 분할 → 원본가 100,100,50,50. 조정 후 연속(100,100,100,100).
    df = _ohlcv(["20210101", "20210102", "20210103", "20210104"],
                [100.0, 100.0, 50.0, 50.0])
    out = adjust_ohlcv(df, splits=[("20210103", 2.0)])
    assert out["close"].tolist() == [100.0, 100.0, 100.0, 100.0]


def test_past_bars_unchanged_no_lookahead():
    # 미래참조 누수 방지: 분할일(20210103) 이전 봉은 원본과 완전히 동일해야 한다.
    df = _ohlcv(["20210101", "20210102", "20210103", "20210104"],
                [100.0, 100.0, 50.0, 50.0])
    out = adjust_ohlcv(df, splits=[("20210103", 2.0)])
    assert out["close"].tolist()[:2] == [100.0, 100.0]  # 소급 변경 없음


def test_volume_adjusted_inversely():
    # 2:1 분할 → 거래 주식수 2배. 주식수 기준 일관성 위해 조정 후 거래량은 1/2.
    df = _ohlcv(["20210102", "20210103"], [100.0, 50.0], volumes=[1000, 2000])
    out = adjust_ohlcv(df, splits=[("20210103", 2.0)])
    assert out["volume"].tolist() == [1000.0, 1000.0]


def test_reverse_split():
    # 1:10 병합(주식수 0.1배) → 원본가 10,100. 조정 후 연속(10,10).
    df = _ohlcv(["20210102", "20210103"], [10.0, 100.0])
    out = adjust_ohlcv(df, splits=[("20210103", 0.1)])
    assert out["close"].tolist() == [10.0, 10.0]


def test_derive_splits_from_raw_vs_adjusted():
    # pykrx back-adjusted 시세와 원본가를 비교해 분할 이벤트(일자, 배수)를 복원한다.
    # 2:1 분할 시 원본가는 100,100,50,50 이고 back-adjusted는 50,50,50,50.
    raw = _ohlcv(["20210101", "20210102", "20210103", "20210104"],
                 [100.0, 100.0, 50.0, 50.0])
    adjusted = _ohlcv(["20210101", "20210102", "20210103", "20210104"],
                      [50.0, 50.0, 50.0, 50.0])
    assert derive_splits(raw, adjusted) == [("20210103", 2.0)]


def test_derive_splits_none_when_no_adjustment():
    raw = _ohlcv(["20210101", "20210102"], [100.0, 101.0])
    assert derive_splits(raw, raw) == []


def test_derive_then_adjust_roundtrip_removes_jump():
    # 복원한 분할을 원본가에 포워드 적용하면 점프가 사라지고 과거 봉은 불변이어야 한다.
    raw = _ohlcv(["20210101", "20210102", "20210103", "20210104"],
                 [100.0, 100.0, 50.0, 50.0])
    adjusted = _ohlcv(["20210101", "20210102", "20210103", "20210104"],
                      [50.0, 50.0, 50.0, 50.0])
    splits = derive_splits(raw, adjusted)
    out = adjust_ohlcv(raw, splits)
    assert out["close"].tolist() == [100.0, 100.0, 100.0, 100.0]


def test_split_not_counted_as_stop_loss():
    # 라벨=돈 불변식: 2:1 분할(원본 -50% 점프)이 손절로 오인되면 안 된다.
    dates = ["20210101", "20210102", "20210103", "20210104",
             "20210105", "20210106", "20210107"]
    raw_close = [100.0, 100.0, 100.0, 50.0, 50.0, 50.0, 50.0]  # 20210104 2:1 분할
    df = _ohlcv(dates, raw_close)

    # 원본가: t=0 진입 시 5일 내 저가 50 <= 손절가 97 → 가짜 손절(-3%).
    raw_ret = make_returns(df, horizon=5).iloc[0]
    assert raw_ret == -0.03

    # 조정 후: 전 구간 100 → 손절 미발동, 실현손익 0.
    adj = adjust_ohlcv(df, splits=[("20210104", 2.0)])
    adj_ret = make_returns(adj, horizon=5).iloc[0]
    assert adj_ret == 0.0
