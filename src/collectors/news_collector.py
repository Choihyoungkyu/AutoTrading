import html
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from src.collectors.krx_collector import KRXCollector

_HEADERS = {"User-Agent": "Mozilla/5.0"}
NAVER_NEWS_API = "https://m.stock.naver.com/api/news/stock/{code}"
GOOGLE_RSS_URL = "https://news.google.com/rss/search"


class NewsCollector:
    """종목 뉴스를 여러 소스에서 모아 정규화한다.

    국내(6자리 코드): 네이버 금융 모바일 뉴스 API + 구글 뉴스.
    최근 N일 필터 + 제목 유사도 기반 중복 제거 후 최신순 반환.
    """

    def __init__(self, krx_collector: KRXCollector = None):
        self.krx = krx_collector or KRXCollector()

    def get_news(self, code: str, days: int = 5, limit: int = 15) -> list:
        items = self._from_naver(code)
        query = self.krx.get_name(code)
        # 원본 매체(네이버)를 먼저 넣어 dedupe 시 우선 보존한다.
        items += self._from_google(query, domestic=True)

        items = self._within_days(items, days)
        items = self._dedupe(items)
        items.sort(key=lambda x: x["published"], reverse=True)
        return items[:limit]

    # --- 소스별 수집 (각 소스는 실패해도 나머지로 진행) ---

    def _from_naver(self, code: str) -> list:
        try:
            resp = requests.get(
                NAVER_NEWS_API.format(code=code), headers=_HEADERS, timeout=15
            )
            resp.raise_for_status()
            clusters = resp.json()
        except (requests.RequestException, ValueError):
            return []

        out = []
        for cluster in clusters:
            for it in cluster.get("items", []):
                published = self._parse_naver_dt(it.get("datetime"))
                title = it.get("titleFull") or it.get("title")
                if not published or not title:
                    continue
                out.append({
                    "title": html.unescape(title),
                    "url": it.get("mobileNewsUrl", ""),
                    "source": it.get("officeName", "네이버뉴스"),
                    "summary": html.unescape(it.get("body", "")),
                    "published": published,
                })
        return out

    def _from_google(self, query: str, domestic: bool) -> list:
        if not query:
            return []
        params = (
            {"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
            if domestic
            else {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
        )
        try:
            resp = requests.get(
                GOOGLE_RSS_URL, params=params, headers=_HEADERS, timeout=15
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except (requests.RequestException, ET.ParseError):
            return []

        out = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            source = item.findtext("source") or "Google News"
            # 구글 뉴스 제목은 "제목 - 언론사" 형태 → 접미사 제거
            suffix = " - " + source
            if title.endswith(suffix):
                title = title[: -len(suffix)]
            try:
                published = self._naive(parsedate_to_datetime(item.findtext("pubDate")))
            except (TypeError, ValueError):
                continue
            if not title:
                continue
            out.append({
                "title": html.unescape(title),
                "url": item.findtext("link") or "",
                "source": source,
                "summary": "",  # 구글 RSS description은 제목·링크뿐이라 본문 요약이 없음
                "published": published,
            })
        return out

    # --- 후처리 (순수 함수, 네트워크 불필요 → 단위 테스트 대상) ---

    @staticmethod
    def _within_days(items: list, days: int, now: datetime = None) -> list:
        ref = (now or datetime.now()).date()
        cutoff = ref - timedelta(days=days)
        return [it for it in items if it["published"].date() >= cutoff]

    @staticmethod
    def _dedupe(items: list) -> list:
        kept = []
        kept_tokens = []
        for it in items:
            tokens = set(NewsCollector._normalize(it["title"]).split())
            if not tokens:
                continue
            if any(NewsCollector._jaccard(tokens, prev) >= 0.6 for prev in kept_tokens):
                continue
            kept.append(it)
            kept_tokens.append(tokens)
        return kept

    @staticmethod
    def _normalize(title: str) -> str:
        text = html.unescape(title).lower()
        return re.sub(r"[^0-9a-z가-힣]+", " ", text).strip()

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        union = a | b
        return len(a & b) / len(union) if union else 0.0

    @staticmethod
    def _naive(dt: datetime) -> datetime:
        # tz-aware(구글)를 로컬 naive로 통일해 정렬·비교 오류를 막는다.
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt

    @staticmethod
    def _parse_naver_dt(value: str):
        try:
            return datetime.strptime(value, "%Y%m%d%H%M")
        except (TypeError, ValueError):
            return None
