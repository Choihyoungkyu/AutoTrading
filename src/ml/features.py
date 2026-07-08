"""ML 신호 파이프라인 T03: 인과적(미래참조 없는) 기술지표 피처 빌더."""

import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator

# 수정주가 caveat: 입력 OHLCV가 수정주가(액면분할/배당 소급 반영)라면
# 과거 봉의 값이 미래 이벤트로 소급 변경되어 T 이후 불변 계약이 깨질 수 있다.
# 이 빌더는 입력을 그대로 신뢰하며 수정주가 여부를 판별/보정하지 않는다.
# 인과성 보장을 원하면 미조정(raw) 시세 또는 시점별 조정계수를 사용해야 한다.


class CausalFeatureBuilder:
    """시점 T까지의 봉만으로 미래참조 없이 기술지표 피처를 계산한다."""

    # 피처 목록(각 열은 "시점 T 이후 데이터에 불변"): 워밍업 이전은 NaN.
    MA_WINDOWS = (5, 20, 50, 60)

    def build_all(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        """각 시점(행)마다 인과적 기술지표 피처 행을 계산해 DataFrame으로 반환한다(워밍업은 NaN)."""
        close = ohlcv["close"].astype(float)
        high = ohlcv["high"].astype(float)
        low = ohlcv["low"].astype(float)
        volume = ohlcv["volume"].astype(float)

        feat = pd.DataFrame(index=ohlcv.index)

        # 이동평균(MA): trailing rolling → 미래 미참조.
        for w in self.MA_WINDOWS:
            feat[f"ma_{w}"] = close.rolling(window=w).mean()

        # RSI(14): ta 내부 EWM은 인과적(과거값만 사용).
        feat["rsi_14"] = RSIIndicator(close=close, window=14).rsi()

        # MACD(12,26,9): EWM 기반이라 인과적.
        macd = MACD(close=close)
        feat["macd_line"] = macd.macd()
        feat["macd_signal"] = macd.macd_signal()
        feat["macd_histogram"] = macd.macd_diff()

        # 볼린저밴드(20,2): 상/중/하단 + %b(밴드 내 상대위치).
        bb = BollingerBands(close=close, window=20, window_dev=2)
        feat["bb_upper"] = bb.bollinger_hband()
        feat["bb_middle"] = bb.bollinger_mavg()
        feat["bb_lower"] = bb.bollinger_lband()
        feat["bb_pct_b"] = bb.bollinger_pband()

        # 스토캐스틱(14,3): rolling min/max → trailing.
        stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
        feat["stoch_k"] = stoch.stoch()
        feat["stoch_d"] = stoch.stoch_signal()

        # OBV와 그 추세(최근 5봉 변화): 누적합은 과거만 사용 → 인과적.
        obv = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
        feat["obv"] = obv
        feat["obv_trend"] = obv - obv.shift(5)

        return feat

    def build_row(self, ohlcv_up_to_T: pd.DataFrame) -> dict:
        """시점 T까지의 OHLCV만으로 마지막 시점의 피처 dict를 반환한다."""
        feat = self.build_all(ohlcv_up_to_T)
        return feat.iloc[-1].to_dict()

    def _feature_columns(self) -> list:
        """생성되는 피처 열 이름 목록을 반환한다(비공개 유틸)."""
        cols = [f"ma_{w}" for w in self.MA_WINDOWS]
        cols += [
            "rsi_14",
            "macd_line",
            "macd_signal",
            "macd_histogram",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "bb_pct_b",
            "stoch_k",
            "stoch_d",
            "obv",
            "obv_trend",
        ]
        return cols
