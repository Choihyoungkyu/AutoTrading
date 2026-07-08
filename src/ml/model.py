"""T05: LightGBM 매수신호 모델 + TreeSHAP 근거.

T03 인과적 피처와 T02 실현손익 라벨로 이진 분류기를 학습하고,
매 예측마다 매수 확률과 TreeSHAP 상위 기여 피처를 근거로 반환한다.

주의: SHAP 근거는 모델이 학습한 '상관관계'이며 시장의 인과가 아니다. 과신 금지.
주의: 입력 가격은 수정주가 미처리(원본가)라 액면분할·증자 구간에 왜곡이 있을 수 있다.
"""

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
import shap

from src.ml.features import CausalFeatureBuilder
from src.ml.labels import make_labels

# SHAP 근거가 인과가 아님을 산출물에 명시하는 고정 문구
SHAP_DISCLAIMER = "근거는 모델이 학습한 상관관계이며 시장의 인과가 아님. 과신 금지."


def build_dataset(ohlcv_frames, label_kwargs: dict = None, feature_builder=None):
    """여러 종목 OHLCV로부터 (X 피처, y 라벨)을 만든다. 피처·라벨 NaN 행은 제외한다."""
    label_kwargs = label_kwargs or {}
    feature_builder = feature_builder or CausalFeatureBuilder()

    xs, ys = [], []
    for ohlcv in ohlcv_frames:
        feats = feature_builder.build_all(ohlcv)
        labels = make_labels(ohlcv, **label_kwargs)
        # 인덱스 정렬 후 결합, 피처/라벨 어느 쪽이든 NaN이면 학습에서 제외
        joined = feats.copy()
        joined["_label"] = labels.values
        joined = joined.dropna()
        if joined.empty:
            continue
        ys.append(joined["_label"].astype(int))
        xs.append(joined.drop(columns=["_label"]))

    if not xs:
        return pd.DataFrame(), pd.Series(dtype=int)

    X = pd.concat(xs, ignore_index=True)
    y = pd.concat(ys, ignore_index=True)
    return X, y


class SignalModel:
    """LightGBM 이진 분류 매수신호 모델. 학습 구간에만 fit하고, 예측마다 SHAP 근거를 낸다."""

    def __init__(self, threshold: float = 0.5, params: dict = None, top_k: int = 3):
        self.threshold = threshold
        self.top_k = top_k
        default = {
            "n_estimators": 100,
            "num_leaves": 15,
            "min_child_samples": 5,
            "random_state": 42,
            "verbose": -1,
        }
        self.params = {**default, **(params or {})}
        self.model = LGBMClassifier(**self.params)
        self.feature_names_ = None
        self._explainer = None

    def fit(self, X: pd.DataFrame, y) -> "SignalModel":
        """학습 구간의 피처/라벨로 모델을 학습한다 (미래참조 방지: 학습 구간에만 fit)."""
        self.feature_names_ = list(X.columns)
        self.model.fit(X, y)
        self._explainer = shap.TreeExplainer(self.model)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """각 행의 매수 확률(양성 클래스, 0~1)을 반환한다."""
        return self.model.predict_proba(X)[:, 1]

    def _shap_row(self, x_row: pd.DataFrame) -> np.ndarray:
        """한 행의 피처별 SHAP 기여도(양성 클래스 기준)를 1차원 배열로 반환한다."""
        values = self._explainer.shap_values(x_row)
        arr = np.asarray(values)
        # shap 버전/모델에 따라 (n, f) 또는 (n, f, class) 또는 list 형태 → 양성 클래스 1행으로 정규화
        if arr.ndim == 3:              # (n, f, n_classes)
            arr = arr[:, :, -1]
        if isinstance(values, list):   # [class0(n,f), class1(n,f)]
            arr = np.asarray(values[-1])
        return arr[0]

    def predict_one(self, x_row: pd.DataFrame) -> dict:
        """단일 시점 예측: 매수/매수 안 함 신호 + 확률 + TreeSHAP 상위 근거."""
        if isinstance(x_row, pd.Series):
            x_row = x_row.to_frame().T
        prob = float(self.predict_proba(x_row)[0])
        signal = "매수" if prob >= self.threshold else "매수 안 함"

        shap_vals = self._shap_row(x_row)
        order = np.argsort(np.abs(shap_vals))[::-1][: self.top_k]
        reasons = [
            {
                "feature": self.feature_names_[i],
                "value": float(x_row.iloc[0, i]),
                "shap": float(shap_vals[i]),
                "direction": "매수쪽" if shap_vals[i] >= 0 else "비매수쪽",
            }
            for i in order
        ]
        return {
            "signal": signal,
            "prob": prob,
            "reasons": reasons,
            "disclaimer": SHAP_DISCLAIMER,
        }
