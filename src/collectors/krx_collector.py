from pykrx import stock
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

NAVER_MAIN_URL = "https://finance.naver.com/item/main.naver"
NAVER_COINFO_URL = "https://finance.naver.com/item/coinfo.naver"
NAVER_GROUP_URL = "https://finance.naver.com/sise/sise_group_detail.naver"
NAVER_QUANT_URL = "https://finance.naver.com/sise/sise_quant.naver"
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
        # 국내 종목만 지원(해외 종목은 추후 개발). 코드가 6자리 숫자인 항목만 반환.
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
        for it in items:
            code = it.get("code")
            if not code or not (code.isdigit() and len(code) == 6):
                continue
            results.append({
                "code": code,
                "name": it.get("name", code),
                "market": it.get("typeName", ""),
            })
            if len(results) >= limit:
                break
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

    def get_top_volume(self, market: str = "KOSPI", limit: int = 100) -> list:
        # 거래량 상위 종목: 네이버 '거래량상위' 페이지(sise_quant) 스크래핑.
        # 현재가·등락률·거래량을 한 번에 제공하고 ETF도 포함(진짜 거래량 순위).
        # 반환: [{"code","name","price","change","changeRate","volume"}] 상위 limit개.
        sosok = {"KOSPI": 0, "KOSDAQ": 1}.get(market.upper(), 0)
        try:
            resp = requests.get(
                NAVER_QUANT_URL, params={"sosok": sosok}, headers=_HEADERS, timeout=15
            )
            resp.encoding = "euc-kr"
            resp.raise_for_status()
        except requests.RequestException:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        out = []
        for tr in soup.select("table.type_2 tr"):
            a = tr.select_one("a.tltle")
            if not a:
                continue
            m = re.search(r"code=(\d{6})", a.get("href", ""))
            if not m:
                continue
            tds = tr.select("td")
            if len(tds) < 6:
                continue
            price = self._to_float(tds[2].get_text())
            rate = self._to_float(tds[4].get_text())  # 등락률(%) — 부호 포함
            # 전일비(금액)는 '상승5'처럼 한글 접두어가 붙어 부호가 없다 → 숫자만 추출 후 등락률 부호 적용
            change = abs(self._to_float(re.sub(r"[^0-9.,]", "", tds[3].get_text())))
            if rate < 0:
                change = -change
            vol_text = tds[5].get_text(strip=True).replace(",", "")
            volume = int(vol_text) if vol_text.isdigit() else None
            out.append({
                "code": m.group(1),
                "name": a.get_text(strip=True),
                "price": price,
                "change": round(change, 2),
                "changeRate": round(rate, 2),
                "volume": volume,
            })
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

    def get_foreign_ratio(self, code: str) -> float:
        # 외국인 지분율(%). pykrx 외국인 소진율 API 최신값. 실패 시 None.
        try:
            today = datetime.today()
            start = (today - timedelta(days=14)).strftime("%Y%m%d")
            end = today.strftime("%Y%m%d")
            df = stock.get_exhaustion_rates_of_foreign_investment(start, end, code)
            if df is None or df.empty:
                return None
            # 컬럼명은 버전마다 다를 수 있어 '한도소진률' 우선, 없으면 마지막 컬럼.
            col = "한도소진률" if "한도소진률" in df.columns else df.columns[-1]
            val = df[col].iloc[-1]
            return round(float(val), 2)
        except Exception:
            return None

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

    def get_market_cap_value(self, code: str):
        # 네이버 시가총액(원 단위). 실패 시 None. 표기 예: "1,674조 9,588" → 1674조9588억.
        try:
            resp = requests.get(NAVER_MAIN_URL, params={"code": code}, headers=_HEADERS, timeout=15)
            resp.encoding = "utf-8"
            resp.raise_for_status()
        except requests.RequestException:
            return None
        el = BeautifulSoup(resp.text, "html.parser").select_one("#_market_sum")
        if el is None:
            return None
        nums = [int(n.replace(",", "")) for n in re.findall(r"[\d,]+", el.get_text(strip=True))
                if n.replace(",", "").isdigit()]
        if not nums:
            return None
        eok = nums[0] * 10000 + nums[1] if len(nums) >= 2 else nums[0]
        return eok * 100_000_000  # 억원 → 원

    def get_company_summary(self, code: str):
        # 네이버 기업개요(회사 정보 탭). 실패 시 None.
        try:
            resp = requests.get(NAVER_COINFO_URL, params={"code": code}, headers=_HEADERS, timeout=15)
            resp.encoding = "euc-kr"
            resp.raise_for_status()
        except requests.RequestException:
            return None
        el = BeautifulSoup(resp.text, "html.parser").select_one("#summary_info")
        if el is None:
            return None
        text = re.sub(r"^기업개요\s*", "", el.get_text(" ", strip=True))
        return text or None

    def get_naver_financials(self, code: str) -> dict:
        # 네이버 '기업실적분석' 테이블에서 연간 매출·이익·이익률·유보율·부채비율을 파싱.
        out = {"annual": [], "retention_ratio": None, "debt_ratio": None}
        try:
            resp = requests.get(NAVER_MAIN_URL, params={"code": code}, headers=_HEADERS, timeout=15)
            resp.encoding = "utf-8"
            resp.raise_for_status()
        except requests.RequestException:
            return out
        cop = BeautifulSoup(resp.text, "html.parser").select_one("div.cop_analysis")
        if cop is None:
            return out

        periods = [th.get_text(strip=True) for th in cop.select("thead th")
                   if re.match(r"\d{4}\.\d{2}", th.get_text(strip=True))]
        # 연간 확정 실적 인덱스: 분기(.03/.06/.09) 구간 전, (E) 추정 제외, 12월 결산
        annual_idx = []
        for i, p in enumerate(periods):
            if re.search(r"\.(03|06|09)", p):
                break
            if p.endswith(".12") and "(E)" not in p:
                annual_idx.append(i)
        annual_idx = annual_idx[:4]

        rows = {}
        for tr in cop.select("tbody tr"):
            th = tr.select_one("th")
            if not th:
                continue
            vals = []
            for td in tr.select("td"):
                t = td.get_text(strip=True).replace(",", "")
                vals.append(float(t) if re.match(r"^-?\d+(\.\d+)?$", t) else None)
            rows[th.get_text(" ", strip=True)] = vals

        def row_for(*keys):
            for label, vals in rows.items():
                if any(k in label for k in keys):
                    return vals
            return None

        def at(row, i, scale=1):
            return row[i] * scale if (row and i < len(row) and row[i] is not None) else None

        rev, op, ni = row_for("매출액"), row_for("영업이익"), row_for("당기순이익")
        opm, nim = row_for("영업이익률"), row_for("순이익률")
        ret, debt = row_for("유보율"), row_for("부채비율")

        out["annual"] = [{
            "year": periods[i].split(".")[0],
            "revenue": at(rev, i, 100_000_000),          # 억원 → 원
            "operating_income": at(op, i, 100_000_000),
            "net_income": at(ni, i, 100_000_000),
            "operating_margin": at(opm, i),
            "net_margin": at(nim, i),
        } for i in annual_idx]
        if annual_idx:
            li = annual_idx[-1]
            out["retention_ratio"] = at(ret, li)
            out["debt_ratio"] = at(debt, li)
        return out

    @staticmethod
    def _to_float(text: str) -> float:
        try:
            return float(text.replace(",", "").replace("%", "").strip())
        except ValueError:
            return 0.0
