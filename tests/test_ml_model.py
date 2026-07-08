"""T05 모델 테스트: 신호/확률/근거 반환 형식 계약 검증 (모델 품질 아님)."""

import numpy as np
import pandas as pd
import pytest

from src.ml.model import SignalModel, build_dataset, SHAP_DISCLAIMER


def _synthetic_separable(n=400, seed=0):
    """f0가 라벨을 강하게 예측하는 합성 피처/라벨 (형식 검증용, 학습이 수렴하도록 분리 가능)."""
    rng = np.random.default_rng(seed)
    f0 = rng.normal(size=n)
    noise = rng.normal(size=(n, 3))
    X = pd.DataFrame(
        {"f0": f0, "f1": noise[:, 0], "f2": noise[:, 1], "f3": noise[:, 2]}
    )
    y = pd.Series((f0 > 0).astype(int))
    return X, y


def _synthetic_ohlcv(n=120, start=100.0, step=0.1):
    dates = [f"2023{i:04d}" for i in range(n)]
    close = start + np.arange(n) * step
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1000 + np.arange(n),
        }
    )


@pytest.fixture
def fitted_model():
    X, y = _synthetic_separable()
    return SignalModel().fit(X, y), X


def test_predict_proba_in_unit_range(fitted_model):
    model, X = fitted_model
    proba = model.predict_proba(X)
    assert proba.shape == (len(X),)
    assert np.all((proba >= 0.0) & (proba <= 1.0))


def test_predict_one_contract(fitted_model):
    model, X = fitted_model
    out = model.predict_one(X.iloc[[0]])
    assert set(out) == {"signal", "prob", "reasons", "disclaimer"}
    assert out["signal"] in ("매수", "매수 안 함")
    assert 0.0 <= out["prob"] <= 1.0
    assert out["disclaimer"] == SHAP_DISCLAIMER


def test_reasons_are_top_k_shap_features(fitted_model):
    model, X = fitted_model
    out = model.predict_one(X.iloc[[0]])
    reasons = out["reasons"]
    assert 1 <= len(reasons) <= model.top_k
    for r in reasons:
        assert set(r) == {"feature", "value", "shap", "direction"}
        assert r["feature"] in model.feature_names_
        assert r["direction"] in ("매수쪽", "비매수쪽")
    # |SHAP| 내림차순 정렬 확인
    abs_shap = [abs(r["shap"]) for r in reasons]
    assert abs_shap == sorted(abs_shap, reverse=True)


def test_threshold_controls_signal(fitted_model):
    model, X = fitted_model
    row = X.iloc[[0]]
    prob = float(model.predict_proba(row)[0])
    model.threshold = 0.0  # 모든 확률이 임계치 이상 → 항상 매수
    assert model.predict_one(row)["signal"] == "매수"
    model.threshold = 1.01  # 어떤 확률도 도달 불가 → 항상 매수 안 함
    assert model.predict_one(row)["signal"] == "매수 안 함"


def test_build_dataset_shape_and_no_nan():
    frames = [_synthetic_ohlcv(seed) for seed in (120, 130)]
    X, y = build_dataset(frames)
    # 16개 인과적 피처 열, 라벨은 0/1, NaN 없음, 길이 일치
    assert X.shape[1] == 16
    assert len(X) == len(y)
    assert not X.isna().any().any()
    assert set(y.unique()).issubset({0, 1})


def test_build_dataset_empty_frames():
    X, y = build_dataset([])
    assert X.empty and y.empty
