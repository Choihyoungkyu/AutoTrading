from concurrent.futures import ThreadPoolExecutor
from src.collectors.krx_collector import KRXCollector


class FinancialAnalyzer:
    def __init__(self, krx_collector: KRXCollector):
        self.krx = krx_collector

    def get_financial_metrics(self, code: str, date: str = None) -> dict:
        metrics = self.krx.get_market_cap(code, date)
        if not metrics:
            return None

        eps = metrics.get("eps", 0)
        bps = metrics.get("bps", 0)
        roe = (eps / bps * 100) if bps > 0 else 0

        # 부채비율은 네이버 '기업실적분석'에서 보완한다(routes._extend_financial).
        debt_ratio = 0

        return {
            "per": metrics.get("per", 0),
            "pbr": metrics.get("pbr", 0),
            "eps": eps,
            "bps": bps,
            "roe": roe,
            "dividend_yield": metrics.get("dividend_yield", 0),
            "debt_ratio": debt_ratio,
            "as_of": metrics.get("as_of"),
        }

    def _peer_metrics(self, code: str) -> dict:
        # 업종 평균 계산용 경량 지표. peer 수가 많아도 빠르다. ROE는 EPS/BPS로 계산.
        try:
            m = self.krx.get_market_cap(code)
        except Exception:
            return {}
        if not m:
            return {}
        bps = m.get("bps", 0)
        return {
            "per": m.get("per", 0),
            "pbr": m.get("pbr", 0),
            "roe": (m.get("eps", 0) / bps * 100) if bps > 0 else 0,
            "dividend_yield": m.get("dividend_yield", 0),
        }

    def get_industry_average(self, peer_codes: list) -> dict:
        per_values = []
        pbr_values = []
        roe_values = []
        dividend_values = []

        # peer별 네이버 조회를 병렬화(순차 시 종목 수만큼 느려짐)
        with ThreadPoolExecutor(max_workers=8) as ex:
            all_metrics = list(ex.map(self._peer_metrics, peer_codes)) if peer_codes else []

        for metrics in all_metrics:
            if not metrics:
                continue
            if metrics.get("per", 0) > 0:
                per_values.append(metrics["per"])
            if metrics.get("pbr", 0) > 0:
                pbr_values.append(metrics["pbr"])
            if metrics.get("roe", 0) > 0:
                roe_values.append(metrics["roe"])
            if metrics.get("dividend_yield", 0) > 0:
                dividend_values.append(metrics["dividend_yield"])

        # 단순평균은 이상치(예: EPS가 작아 PER이 수천인 종목)에 크게 왜곡되므로
        # 이상치에 강건한 중앙값(median)을 사용한다.
        return {
            "per": self._median(per_values),
            "pbr": self._median(pbr_values),
            "roe": self._median(roe_values),
            "dividend_yield": self._median(dividend_values),
            "peer_count": len(per_values),
        }

    @staticmethod
    def _median(values: list) -> float:
        if not values:
            return 0
        s = sorted(values)
        n = len(s)
        mid = n // 2
        return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2

    def determine_verdict(self, metrics: dict, industry_avg: dict) -> str:
        per_lower = metrics.get("per", 0) < industry_avg.get("per", float("inf"))
        pbr_lower = metrics.get("pbr", 0) < industry_avg.get("pbr", float("inf"))
        per_higher = metrics.get("per", 0) > industry_avg.get("per", 0)
        pbr_higher = metrics.get("pbr", 0) > industry_avg.get("pbr", 0)

        if per_lower and pbr_lower:
            return "저평가"
        elif per_higher and pbr_higher:
            return "고평가"
        else:
            return "중립"

    def analyze(self, code: str) -> dict:
        metrics = self.get_financial_metrics(code)
        if not metrics:
            return None

        # 조회 종목의 업종을 파악해 동일업종 종목으로 업계 평균을 낸다.
        # 업종/peer 조회 실패 시 폴백 없이 "조회 실패"로 표시한다.
        industry = self.krx.get_industry(code)
        peers = [c for c in self.krx.get_industry_peers(industry.get("no")) if c != code]
        industry_avg = self.get_industry_average(peers)
        industry_ok = bool(industry.get("name")) and industry_avg.get("peer_count", 0) > 0
        verdict = self.determine_verdict(metrics, industry_avg) if industry_ok else "조회 실패"

        return {
            "code": code,
            "as_of": metrics.get("as_of"),
            "per": round(metrics["per"], 2),
            "pbr": round(metrics["pbr"], 2),
            "roe": round(metrics["roe"], 2),
            "eps": round(metrics["eps"], 2),
            "bps": round(metrics["bps"], 2),
            "debt_ratio": round(metrics["debt_ratio"], 2),
            "dividend_yield": round(metrics["dividend_yield"], 2),
            "industry_name": industry.get("name") if industry_ok else None,
            "industry_avg": {
                "per": round(industry_avg["per"], 2),
                "pbr": round(industry_avg["pbr"], 2),
                "roe": round(industry_avg["roe"], 2),
                "dividend_yield": round(industry_avg["dividend_yield"], 2),
                "peer_count": industry_avg.get("peer_count", 0),
            } if industry_ok else None,
            "verdict": verdict,
        }
