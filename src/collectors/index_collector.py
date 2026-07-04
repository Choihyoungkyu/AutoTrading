import requests

# 주요 지수(국내·해외) 수집기.
# 이 환경에서 PYKRX 지수 API와 yfinance는 차단/오류이므로,
# 프로젝트가 이미 재무·뉴스에 쓰는 네이버 금융 API를 사용한다.
#   국내: polling.finance.naver.com (KOSPI/KOSDAQ)
#   해외: api.stock.naver.com/index/<symbol>/basic (.IXIC/.INX/.DJI)


class IndexCollector:
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    # (표시명, 시장구분, 네이버 심볼)
    DOMESTIC = [("코스피", "KOSPI"), ("코스닥", "KOSDAQ")]
    WORLD = [("나스닥", ".IXIC"), ("S&P500", ".INX"), ("다우", ".DJI")]

    def get_indices(self) -> list:
        return [self._domestic(name, sym) for name, sym in self.DOMESTIC] + [
            self._world(name, sym) for name, sym in self.WORLD
        ]

    def _domestic(self, name: str, symbol: str) -> dict:
        try:
            url = f"https://polling.finance.naver.com/api/realtime/domestic/index/{symbol}"
            d = requests.get(url, headers=self.HEADERS, timeout=8).json()["datas"][0]
            return self._pack(name, d)
        except Exception as e:
            return {"name": name, "error": str(e)}

    def _world(self, name: str, symbol: str) -> dict:
        try:
            url = f"https://api.stock.naver.com/index/{symbol}/basic"
            d = requests.get(url, headers=self.HEADERS, timeout=8).json()
            return self._pack(name, d)
        except Exception as e:
            return {"name": name, "error": str(e)}

    def _pack(self, name: str, d: dict) -> dict:
        price = self._num(d.get("closePrice"))
        change = self._num(d.get("compareToPreviousClosePrice"))
        rate = self._num(d.get("fluctuationsRatio"))
        # 등락 방향: 네이버 risefall(1·2=상승, 4·5=하락, 3=보합) 우선, 없으면 부호로 판정
        rf = str(d.get("compareToPreviousPrice", {}).get("code", "")) if isinstance(
            d.get("compareToPreviousPrice"), dict
        ) else str(d.get("risefall", ""))
        if rf in ("4", "5") and change > 0:
            change = -change
            rate = -abs(rate)
        return {
            "name": name,
            "price": price,
            "change": round(change, 2),
            "changeRate": round(rate, 2),
        }

    @staticmethod
    def _num(v) -> float:
        if v is None:
            return 0.0
        try:
            return float(str(v).replace(",", ""))
        except (ValueError, TypeError):
            return 0.0
