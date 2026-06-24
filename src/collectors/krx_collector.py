from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta


class KRXCollector:
    def get_ohlcv(self, code: str, start: str = None, end: str = None) -> pd.DataFrame:
        today = datetime.today()
        if end is None:
            end = today.strftime("%Y%m%d")
        if start is None:
            start = (today - timedelta(days=30)).strftime("%Y%m%d")

        df = stock.get_market_ohlcv(start, end, code)
        if df.empty:
            return pd.DataFrame()

        df.columns = ["open", "high", "low", "close", "volume", "change"]
        df.index.name = "date"
        df = df.reset_index()
        df["date"] = df["date"].astype(str)
        df["code"] = code
        return df

    def get_market_cap(self, code: str, date: str = None) -> dict:
        if date is None:
            date = datetime.today().strftime("%Y%m%d")
        df = stock.get_market_fundamental(date, date, code)
        if df.empty:
            return {}
        row = df.iloc[0]
        return {
            "per": float(row.get("PER", 0)),
            "pbr": float(row.get("PBR", 0)),
            "dividend_yield": float(row.get("DIV", 0)),
            "eps": float(row.get("EPS", 0)),
        }
