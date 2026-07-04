import pandas as pd
from datetime import datetime, timedelta
from src.collectors.krx_collector import KRXCollector
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands


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

        return {
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
