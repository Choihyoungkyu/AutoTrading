import yfinance as yf
import pandas as pd
import time


class YFinanceCollector:
    def __init__(self, retries: int = 3, retry_delay: int = 2):
        self.retries = retries
        self.retry_delay = retry_delay

    def get_ohlcv(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        for attempt in range(self.retries):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period)
                if not df.empty:
                    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
                    df.columns = ["open", "high", "low", "close", "volume"]
                    df.index.name = "date"
                    df = df.reset_index()
                    df["date"] = df["date"].dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                    df["symbol"] = symbol
                    return df
            except Exception as e:
                if attempt < self.retries - 1:
                    time.sleep(self.retry_delay)
                    continue
        raise ValueError(f"No data found for symbol: {symbol}")

    def get_info(self, symbol: str) -> dict:
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.info
            return {
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "per": info.get("trailingPE"),
                "pbr": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
            }
        except Exception as e:
            return {}

    def get_news(self, symbol: str) -> list:
        ticker = yf.Ticker(symbol)
        try:
            return ticker.news
        except Exception:
            return []
