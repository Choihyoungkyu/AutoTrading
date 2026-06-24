# pykrx는 import 시점에 KRX_ID/KRX_PW 환경변수로 KRX 로그인을 시도하므로,
# pykrx를 import하기 전에 .env를 먼저 로드해야 한다.
from dotenv import load_dotenv
load_dotenv()

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
        # KRX(pykrx) 재무 지표. KRX_ID/KRX_PW 환경변수(.env)로 로그인 필요.
        # date를 주면 해당 시점, 없으면 최근 영업일 기준값을 가져온다.
        if date is not None:
            start = end = date
        else:
            today = datetime.today()
            end = today.strftime("%Y%m%d")
            start = (today - timedelta(days=7)).strftime("%Y%m%d")

        df = stock.get_market_fundamental(start, end, code)
        if df.empty:
            return {}

        row = df.iloc[-1]
        idx = df.index[-1]
        as_of = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
        return {
            "per": float(row.get("PER", 0)),
            "pbr": float(row.get("PBR", 0)),
            "dividend_yield": float(row.get("DIV", 0)),
            "eps": float(row.get("EPS", 0)),
            "bps": float(row.get("BPS", 0)),
            "as_of": as_of,
        }
