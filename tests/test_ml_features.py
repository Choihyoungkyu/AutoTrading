"""T03 인과적 피처 빌더 테스트: T-불변성 / 워밍업 NaN / build_row 일치."""

import numpy as np
import pandas as pd
import pandas.testing as pdt

from src.ml.features import CausalFeatureBuilder


def _synth_ohlcv(n: int, seed: int = 0) -> pd.DataFrame:
    """재현 가능한 합성 OHLCV(정수 인덱스, 오름차순 날짜)를 만든다."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="D").strftime("%Y-%m-%d")
    close = 10000 + np.cumsum(rng.normal(0, 100, n))
    close = np.abs(close) + 1000  # 양수 보장
    high = close + rng.uniform(10, 200, n)
    low = close - rng.uniform(10, 200, n)
    open_ = close + rng.normal(0, 50, n)
    volume = rng.integers(10000, 100000, n).astype(float)
    return pd.DataFrame(
        {
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def test_t_invariance_no_lookahead():
    """미래 봉 추가 후 재계산해도 원래 시점의 피처 행이 동일해야 한다(미래참조 부재)."""
    builder = CausalFeatureBuilder()
    base = _synth_ohlcv(120, seed=1)
    future = _synth_ohlcv(40, seed=2)  # 다른 시드의 미래 봉
    extended = pd.concat([base, future], ignore_index=True)

    feat_base = builder.build_all(base)
    feat_ext = builder.build_all(extended)

    # 원래 구간(0..119)의 피처가 미래 봉 추가에 불변임을 검증(NaN 포함 비교).
    pdt.assert_frame_equal(feat_base, feat_ext.iloc[: len(base)])


def test_warmup_period_is_nan():
    """워밍업 구간(MA/RSI 등 주기 이전)은 명시적으로 NaN이어야 한다."""
    builder = CausalFeatureBuilder()
    df = _synth_ohlcv(80, seed=3)
    feat = builder.build_all(df)

    # MA: window-1 이전은 NaN, 이후는 값 존재.
    assert feat["ma_5"].iloc[:4].isna().all()
    assert not np.isnan(feat["ma_5"].iloc[4])
    assert feat["ma_50"].iloc[:49].isna().all()
    assert not np.isnan(feat["ma_50"].iloc[49])
    assert feat["ma_60"].iloc[:59].isna().all()

    # RSI(14): 첫 봉은 계산 불가라 NaN, 워밍업 이후 값 존재.
    assert np.isnan(feat["rsi_14"].iloc[0])
    assert not np.isnan(feat["rsi_14"].iloc[-1])

    # 스토캐스틱(14): 초반 NaN.
    assert feat["stoch_k"].iloc[:13].isna().all()


def test_build_row_matches_build_all_at_T():
    """build_row(df[:T+1])의 결과가 build_all(df)의 T행과 일치해야 한다."""
    builder = CausalFeatureBuilder()
    df = _synth_ohlcv(100, seed=4)
    feat_all = builder.build_all(df)

    for T in (49, 59, 70, 99):
        row = builder.build_row(df.iloc[: T + 1])
        expected = feat_all.iloc[T].to_dict()
        assert row.keys() == expected.keys()
        for k in expected:
            a, b = row[k], expected[k]
            if pd.isna(b):
                assert pd.isna(a), f"{k}@T={T}: {a} != NaN"
            else:
                assert a == b or np.isclose(a, b), f"{k}@T={T}: {a} != {b}"


def test_feature_columns_present():
    """계약된 피처 열이 모두 출력에 존재해야 한다."""
    builder = CausalFeatureBuilder()
    feat = builder.build_all(_synth_ohlcv(70, seed=5))
    for col in builder._feature_columns():
        assert col in feat.columns
