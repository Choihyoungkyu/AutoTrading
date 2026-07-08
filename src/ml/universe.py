from dotenv import load_dotenv

# pykrx 1.2.8은 import 시점에 KRX_ID/KRX_PW로 로그인한다(시장전체·지수 엔드포인트는
# KRX 로그인 필수 — 익명 요청은 400 LOGOUT). pykrx import 전에 .env를 로드해야 한다.
load_dotenv()

from pykrx import stock
from src.collectors.krx_collector import KRXCollector

# caveat: pykrx의 get_market_ohlcv_by_ticker는 수정주가(액면분할·증자 소급조정)를
# 처리하지 않은 원본가를 준다 → 가격 점프가 있을 수 있으나, 유니버스는 거래대금
# 순위만 쓰므로 영향이 제한적이다. 가격 자체를 쓰는 하위 단계에서 별도 조정이 필요하다.


class UniverseSelector:
    """point-in-time 유동성(거래대금) 상위 종목 유니버스를 선정한다."""

    def __init__(self, collector=None):
        # DI 관례: collector 미지정 시 기본 KRXCollector 사용.
        self.collector = collector or KRXCollector()

    def get_universe(self, as_of: str, top_n: int = 200, market: str = "KOSPI") -> list[str]:
        """as_of(YYYYMMDD) 그 날짜 데이터만으로 거래대금 상위 top_n 종목코드 리스트 반환."""
        df = self._fetch_ohlcv_by_ticker(as_of, market)
        if df is None or df.empty or "거래대금" not in df.columns:
            return []
        ranked = df.sort_values("거래대금", ascending=False)
        codes = ranked.index[:top_n]
        return [str(code).zfill(6) for code in codes]

    def get_universe_band(self, as_of: str, start_rank: int, end_rank: int,
                          market: str = "KOSPI", min_value=None) -> list[str]:
        """as_of 그 시점 데이터만으로 거래대금 내림차순 [start_rank, end_rank) 밴드 반환.

        0-기반 순위. min_value가 주어지면 거래대금 < min_value 종목을 밴드 슬라이스
        전에 제외한다(극저유동성·슬리피지 방지). get_universe와 동일한 point-in-time.
        """
        df = self._fetch_ohlcv_by_ticker(as_of, market)
        if df is None or df.empty or "거래대금" not in df.columns:
            return []
        ranked = df.sort_values("거래대금", ascending=False)
        if min_value is not None:
            ranked = ranked[ranked["거래대금"] >= min_value]
        codes = ranked.index[start_rank:end_rank]
        return [str(code).zfill(6) for code in codes]

    def _fetch_ohlcv_by_ticker(self, as_of: str, market: str):
        # 해당일 전 종목 OHLCV+거래대금(종목코드 인덱스). 실패 시 None.
        try:
            return stock.get_market_ohlcv_by_ticker(as_of, market)
        except Exception:
            return None
