import pandas as pd
from datetime import datetime, timedelta
from src.collectors.krx_collector import KRXCollector
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator


class ChartAnalyzer:
    def __init__(self, krx_collector: KRXCollector = None):
        self.krx = krx_collector or KRXCollector()

    def analyze(self, code: str) -> dict:
        """주식 종목의 기술적 분석 수행 (MA, RSI, MACD, 볼린저밴드)"""
        # 국내 시세는 다른 섹션과 동일하게 PYKRX로 조회한다.
        # 지표 계산에 최소 50거래일이 필요하므로 약 1년(주말/휴장 포함 400일)을 요청한다.
        today = datetime.today()
        start = (today - timedelta(days=400)).strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
        df = self.krx.get_ohlcv(code, start=start, end=end)
        if df is None or df.empty:
            return None

        if len(df) < 50:
            return None

        indicators = self._calculate_indicators(df)
        signal, confidence = self._determine_signal(indicators)

        as_of = str(df["date"].iloc[-1]) if "date" in df.columns else str(df.index[-1])

        result = {
            "code": code,
            "as_of": as_of,
            "ma_20": round(indicators["ma_20"], 2),
            "ma_50": round(indicators["ma_50"], 2),
            "rsi": round(indicators["rsi"], 2),
            "macd": {
                "line": round(indicators["macd_line"], 2),
                "signal": round(indicators["macd_signal"], 2),
                "histogram": round(indicators["macd_histogram"], 2),
            },
            "bollinger_band": {
                "upper": round(indicators["bb_upper"], 2),
                "middle": round(indicators["bb_middle"], 2),
                "lower": round(indicators["bb_lower"], 2),
            },
            "signal": signal,
            "confidence": round(confidence, 2),
        }

        # --- 확장 필드(하위호환): 실패해도 기존 응답은 유지 ---
        try:
            result.update(self._extended(df, indicators, close_price=float(df["close"].iloc[-1])))
        except Exception:
            pass

        return result

    def _extended(self, df, indicators, close_price):
        """ma_5 / stochastic / obv / indicators(6개 개별 판정) / score."""
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # MA5, MA60(정배열 판정용)
        ma_5 = close.rolling(window=5).mean().iloc[-1]
        ma_60 = close.rolling(window=60).mean().iloc[-1] if len(df) >= 60 else None

        # 스토캐스틱(14, 3)
        stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
        k = stoch.stoch().iloc[-1]
        d = stoch.stoch_signal().iloc[-1]

        # OBV: 최신값 + 추세(최근 5봉 기울기)
        obv_series = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
        obv_last = obv_series.iloc[-1]
        obv_prev = obv_series.iloc[-6] if len(obv_series) >= 6 else obv_series.iloc[0]
        obv_rising = obv_last > obv_prev

        rsi = indicators["rsi"]
        ma_20 = indicators["ma_20"]
        ma_50 = indicators["ma_50"]
        macd_line = indicators["macd_line"]
        macd_signal = indicators["macd_signal"]
        bb_upper = indicators["bb_upper"]
        bb_lower = indicators["bb_lower"]

        items = []

        # 1) RSI(14)
        if rsi < 30:
            items.append({"name": "RSI(14)", "value": f"{rsi:.1f}", "state": "과매도", "signal": "buy"})
        elif rsi > 70:
            items.append({"name": "RSI(14)", "value": f"{rsi:.1f}", "state": "과매수", "signal": "sell"})
        else:
            items.append({"name": "RSI(14)", "value": f"{rsi:.1f}", "state": "중립", "signal": "hold"})

        # 2) MACD(12,26,9)
        if macd_line > macd_signal:
            items.append({"name": "MACD(12,26,9)", "value": f"{macd_line:.1f}", "state": "골든크로스", "signal": "buy"})
        elif macd_line < macd_signal:
            items.append({"name": "MACD(12,26,9)", "value": f"{macd_line:.1f}", "state": "데드크로스", "signal": "sell"})
        else:
            items.append({"name": "MACD(12,26,9)", "value": f"{macd_line:.1f}", "state": "중립", "signal": "hold"})

        # 3) 이동평균선 (정배열: MA5>MA20>MA60)
        ma_val = f"MA20 {ma_20:,.0f}"
        if ma_60 is not None and ma_5 > ma_20 > ma_60:
            items.append({"name": "이동평균선", "value": ma_val, "state": "정배열", "signal": "buy"})
        elif ma_60 is not None and ma_5 < ma_20 < ma_60:
            items.append({"name": "이동평균선", "value": ma_val, "state": "역배열", "signal": "sell"})
        elif ma_20 > ma_50:
            items.append({"name": "이동평균선", "value": ma_val, "state": "정배열", "signal": "buy"})
        elif ma_20 < ma_50:
            items.append({"name": "이동평균선", "value": ma_val, "state": "역배열", "signal": "sell"})
        else:
            items.append({"name": "이동평균선", "value": ma_val, "state": "혼조", "signal": "hold"})

        # 4) 볼린저밴드 (하단 근접 buy / 상단 근접 sell)
        band = bb_upper - bb_lower
        near = band * 0.1 if band > 0 else 0
        if close_price <= bb_lower + near:
            items.append({"name": "볼린저밴드", "value": f"{close_price:,.0f}", "state": "하단", "signal": "buy"})
        elif close_price >= bb_upper - near:
            items.append({"name": "볼린저밴드", "value": f"{close_price:,.0f}", "state": "상단", "signal": "sell"})
        else:
            items.append({"name": "볼린저밴드", "value": f"{close_price:,.0f}", "state": "중앙", "signal": "hold"})

        # 5) 스토캐스틱
        if k < 20:
            items.append({"name": "스토캐스틱", "value": f"K {k:.1f}", "state": "과매도", "signal": "buy"})
        elif k > 80:
            items.append({"name": "스토캐스틱", "value": f"K {k:.1f}", "state": "과매수", "signal": "sell"})
        else:
            items.append({"name": "스토캐스틱", "value": f"K {k:.1f}", "state": "중립", "signal": "hold"})

        # 6) 거래량(OBV)
        items.append({
            "name": "거래량(OBV)",
            "value": f"{obv_last:,.0f}",
            "state": "상승추세" if obv_rising else "하락추세",
            "signal": "buy" if obv_rising else "sell",
        })

        # 종합 점수: 50 + (buy-sell)/count*50 → 0~100
        buys = sum(1 for i in items if i["signal"] == "buy")
        sells = sum(1 for i in items if i["signal"] == "sell")
        count = len(items)
        score = round(50 + (buys - sells) / count * 50) if count else 50
        score = max(0, min(100, score))

        return {
            "ma_5": round(float(ma_5), 2) if ma_5 == ma_5 else None,
            "stochastic": {"k": round(float(k), 2), "d": round(float(d), 2)}
            if (k == k and d == d) else None,
            "obv": int(obv_last) if obv_last == obv_last else None,
            "score": score,
            "indicators": items,
        }

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """기술적 지표 계산 (ta 라이브러리 활용)"""
        close = df["close"]

        # MA20, MA50 (ta에 SMAIndicator 없음 → pandas rolling 사용)
        ma_20 = close.rolling(window=20).mean().iloc[-1]
        ma_50 = close.rolling(window=50).mean().iloc[-1]

        # RSI (14주기)
        rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]

        # MACD
        macd = MACD(close=close)
        macd_line = macd.macd().iloc[-1]
        macd_signal = macd.macd_signal().iloc[-1]
        macd_histogram = macd.macd_diff().iloc[-1]

        # 볼린저밴드 (20주기, 2 표준편차)
        bb = BollingerBands(close=close, window=20, window_dev=2)
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_middle = bb.bollinger_mavg().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]

        return {
            "ma_20": ma_20,
            "ma_50": ma_50,
            "rsi": rsi,
            "macd_line": macd_line,
            "macd_signal": macd_signal,
            "macd_histogram": macd_histogram,
            "bb_upper": bb_upper,
            "bb_middle": bb_middle,
            "bb_lower": bb_lower,
        }

    def _determine_signal(self, indicators: dict) -> tuple:
        """Buy/Sell/Hold 신호 판단 및 신뢰도 계산"""
        rsi = indicators["rsi"]
        ma_20 = indicators["ma_20"]
        ma_50 = indicators["ma_50"]

        # Buy: RSI < 30 AND MA20 > MA50
        if rsi < 30 and ma_20 > ma_50:
            confidence = min(1.0, ((30 - rsi) / 30 + (ma_20 - ma_50) / ma_50) / 2)
            return "buy", confidence

        # Sell: RSI > 70 AND MA20 < MA50
        if rsi > 70 and ma_20 < ma_50:
            confidence = min(1.0, ((rsi - 70) / 30 + (ma_50 - ma_20) / ma_50) / 2)
            return "sell", confidence

        # Hold
        return "hold", 0.5
