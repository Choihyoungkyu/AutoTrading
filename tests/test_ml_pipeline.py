"""C 준비: 실험 하네스(pipeline) 순수 로직 테스트 (네트워크 없이).

C1(재무)·C2(중소형주)가 공유할 패널 조립·폴드 평가 로직을 검증한다. 지수 수익은
주입식(index_ret_fn)이라 네트워크 없이 테스트한다.
"""
import numpy as np
import pandas as pd

from src.ml.pipeline import panel_rows_for, evaluate_folds
from src.ml.features import CausalFeatureBuilder


def _synth_ohlcv(n=200):
    # 완만한 상승 + 잡음. 피처 워밍업(≥60)을 넘기도록 충분히 길게.
    base = np.linspace(100, 140, n)
    close = base + np.sin(np.arange(n) / 3.0)
    dates = pd.date_range("2019-01-01", periods=n, freq="D").strftime("%Y%m%d")
    return pd.DataFrame({
        "date": dates, "open": close, "high": close + 1,
        "low": close - 1, "close": close, "volume": np.full(n, 1000.0),
    })


def test_panel_rows_includes_features_labels_and_extra():
    ohlcv = _synth_ohlcv()
    feature_cols = ["ma_5", "rsi_14", "fund_per"]  # 차트 2개 + 재무 1개(extra)

    def extra_fn(code, df):
        return pd.DataFrame({"fund_per": np.full(len(df), 10.0)})

    rows = panel_rows_for(ohlcv, horizon=5, cost=0.007, feature_cols=feature_cols,
                          code="TEST", builder=CausalFeatureBuilder(), extra_feature_fn=extra_fn)
    for col in feature_cols + ["label", "gross_ret", "code"]:
        assert col in rows.columns
    assert not rows[feature_cols + ["label", "gross_ret"]].isna().any().any()
    assert (rows["fund_per"] == 10.0).all()


def test_evaluate_folds_skips_lockbox_and_uses_injected_index():
    # 두 종목 × 두 해. 폴드2(2020)는 락박스 → 평가 제외. 지수는 주입 스텁.
    frames = []
    for code in ["A", "B"]:
        o = _synth_ohlcv(260)
        o["date"] = (list(pd.date_range("2019-01-01", periods=130, freq="D").strftime("%Y%m%d"))
                     + list(pd.date_range("2020-01-01", periods=130, freq="D").strftime("%Y%m%d")))
        r = panel_rows_for(o, horizon=5, cost=0.007, feature_cols=["ma_5", "rsi_14"],
                           code=code, builder=CausalFeatureBuilder())
        frames.append(r)
    panel = pd.concat(frames, ignore_index=True)

    out = evaluate_folds(
        panel,
        folds=[("20190101", "20191231"), ("20200101", "20201231")],
        feature_cols=["ma_5", "rsi_14"], embargo=5, horizon=5, cost=0.007,
        lockbox=("20200101", "20201231"),
        index_ret_fn=lambda s, e: 0.0,
    )
    # 락박스(2020) 제외 → 평가 폴드는 최대 1개(2019). 지수수익은 주입값 0.0.
    assert all(fm["index_ret"] == 0.0 for fm in out["fold_metrics"])
    assert any(f["is_lockbox"] for f in out["folds"])
    assert all(not_lockbox_evaluated(out) for _ in [0])


def not_lockbox_evaluated(out):
    # 평가된 폴드 수는 락박스가 아닌 폴드 수 이하여야 한다.
    n_non_lockbox = sum(1 for f in out["folds"] if not f["is_lockbox"])
    return len(out["fold_metrics"]) <= n_non_lockbox
