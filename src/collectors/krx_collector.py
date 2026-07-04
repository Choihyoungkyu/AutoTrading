from pykrx import stock
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

NAVER_MAIN_URL = "https://finance.naver.com/item/main.naver"
NAVER_GROUP_URL = "https://finance.naver.com/sise/sise_group_detail.naver"
NAVER_AC_URL = "https://ac.stock.naver.com/ac"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


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

    def get_name(self, code: str) -> str:
        # 구글 뉴스 검색 쿼리용 종목명. 실패 시 코드를 그대로 반환한다.
        try:
            name = stock.get_market_ticker_name(code)
            return name or code
        except Exception:
            return code

    def search(self, keyword: str, limit: int = 5) -> list:
        # 종목 검색: 로그인 불필요한 네이버 자동완성 API 사용.
        # 반환: [{"code","name","market"}] 상위 limit개. 실패 시 [].
        try:
            resp = requests.get(
                NAVER_AC_URL,
                params={"q": keyword, "target": "stock"},
                headers=_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except (requests.RequestException, ValueError):
            return []

        results = []
        for it in items[:limit]:
            code = it.get("code")
            if not code:
                continue
            results.append({
                "code": code,
                "name": it.get("name", code),
                "market": it.get("typeName", ""),
            })
        return results

    def get_industry(self, code: str) -> dict:
        # 네이버 종목 페이지의 업종 링크(sise_group_detail?type=upjong&no=NNN)에서
        # 업종 번호와 업종명을 추출한다. 실패 시 {}.
        try:
            resp = requests.get(
                NAVER_MAIN_URL, params={"code": code}, headers=_HEADERS, timeout=15
            )
            # 종목 메인 페이지는 UTF-8(응답 헤더 charset) — 인코딩을 강제하지 않는다.
        except requests.RequestException:
            return {}

        a = BeautifulSoup(resp.text, "html.parser").select_one(
            "a[href*='sise_group_detail'][href*='upjong']"
        )
        if not a:
            return {}
        m = re.search(r"no=(\d+)", a.get("href", ""))
        return {"no": m.group(1) if m else None, "name": a.get_text(strip=True)}

    def get_industry_peers(self, no: str, limit: int = 15) -> list:
        # 업종 상세 페이지에서 동일업종 종목 코드 목록(상위 limit개)을 가져온다.
        if not no:
            return []
        try:
            resp = requests.get(
                NAVER_GROUP_URL,
                params={"type": "upjong", "no": no},
                headers=_HEADERS,
                timeout=15,
            )
            resp.encoding = "euc-kr"
        except requests.RequestException:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        seen, out = set(), []
        for a in soup.select("table a[href*='/item/main']"):
            m = re.search(r"code=(\d{6})", a.get("href", ""))
            if not m:
                continue
            code = m.group(1)
            if code in seen:
                continue
            seen.add(code)
            out.append(code)
            if len(out) >= limit:
                break
        return out

    def get_quote(self, code: str) -> dict:
        # 관심 종목 목록용 경량 시세(현재가·등락률). 네이버 실시간 API.
        try:
            url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
            d = requests.get(url, headers=_HEADERS, timeout=8).json()["datas"][0]
        except (requests.RequestException, ValueError, KeyError, IndexError):
            return {}

        price = self._to_float(d.get("closePrice"))
        change = self._to_float(d.get("compareToPreviousClosePrice"))
        rate = self._to_float(d.get("fluctuationsRatio"))
        # 등락 방향: code 4·5 = 하락(네이버 change/ratio는 부호 없이 오므로 보정)
        direction = str((d.get("compareToPreviousPrice") or {}).get("code", ""))
        if direction in ("4", "5"):
            change, rate = -abs(change), -abs(rate)
        return {
            "code": code,
            "name": d.get("stockName", code),
            "price": price,
            "change": round(change, 2),
            "changeRate": round(rate, 2),
        }

    def get_market_cap(self, code: str, date: str = None) -> dict:
        # KRX 재무 엔드포인트는 로그인을 요구(익명 요청에 400 LOGOUT)하므로,
        # 로그인이 필요 없는 네이버 금융 종목 페이지에서 최신 PER/PBR/EPS/BPS/
        # 배당수익률을 가져온다. PER/PBR은 현재가 기준으로 계산된 값이다.
        # (date 인자는 호환성을 위해 유지하나, 네이버는 최신값만 제공한다.)
        try:
            resp = requests.get(
                NAVER_MAIN_URL, params={"code": code}, headers=_HEADERS, timeout=15
            )
            resp.raise_for_status()
        except requests.RequestException:
            return {}

        table = BeautifulSoup(resp.text, "html.parser").select_one(
            "div.aside_invest_info table.per_table"
        )
        if table is None:
            return {}

        result = {"per": 0.0, "pbr": 0.0, "dividend_yield": 0.0, "eps": 0.0, "bps": 0.0}
        for row in table.select("tr"):
            th, td = row.find("th"), row.find("td")
            if not th or not td:
                continue
            label = th.get_text(strip=True)
            values = [self._to_float(em.get_text()) for em in td.select("em")]
            if label.startswith("PER") and "EPS" in label and len(values) >= 2:
                result["per"], result["eps"] = values[0], values[1]
            elif label.startswith("PBR") and len(values) >= 2:
                result["pbr"], result["bps"] = values[0], values[1]
            elif label.startswith("배당수익률") and values:
                result["dividend_yield"] = values[0]
        return result

    @staticmethod
    def _to_float(text: str) -> float:
        try:
            return float(text.replace(",", "").replace("%", "").strip())
        except ValueError:
            return 0.0
