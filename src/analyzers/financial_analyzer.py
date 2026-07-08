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

    def _collect_peer_metrics(self, peer_codes: list) -> list:
        # peer별 조회를 병렬화(순차 시 종목 수만큼 느려짐). 빈 결과는 제거.
        with ThreadPoolExecutor(max_workers=8) as ex:
            all_metrics = list(ex.map(self._peer_metrics, peer_codes)) if peer_codes else []
        return [m for m in all_metrics if m]

    def get_industry_average(self, peer_codes: list) -> dict:
        # 하위호환 편의 메서드: peer 코드로 중앙값 요약을 바로 계산.
        return self._industry_average(self._collect_peer_metrics(peer_codes))

    def _industry_average(self, peer_metrics: list) -> dict:
        per_values = []
        pbr_values = []
        roe_values = []
        dividend_values = []

        for metrics in peer_metrics:
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

    @staticmethod
    def _percentile(value, peer_values: list, higher_is_better: bool):
        # value가 업종 peer 대비 상위 몇 %인지 0~100(높을수록 우수).
        # KRX 밸류업 지수의 '산업군 내 순위비율' 방식. 이상치는 순위에만 영향(강건).
        vals = [v for v in peer_values if v is not None and v > 0]
        if value is None or value <= 0 or not vals:
            return None
        if higher_is_better:
            wins = sum(1 for v in vals if value > v)
        else:
            wins = sum(1 for v in vals if value < v)
        ties = sum(1 for v in vals if value == v)
        return round((wins + 0.5 * ties) / len(vals) * 100)

    def score_valuation(self, metrics: dict, peer_metrics: list) -> dict:
        """업종 peer 대비 순위비율(0~100)로 재무 점수 산출. KRX 밸류업 방식.
        PER·PBR은 낮을수록, ROE·배당은 높을수록 높은 점수.
        - valuation_score: PER+PBR 평균 → 저평가/고평가 판정
        - score: 4개 지표 평균 → 추천 엔진 반영(종합 매력도)"""
        peers = [m for m in peer_metrics if m]
        per = self._percentile(metrics.get("per"), [m.get("per") for m in peers], higher_is_better=False)
        pbr = self._percentile(metrics.get("pbr"), [m.get("pbr") for m in peers], higher_is_better=False)
        roe = self._percentile(metrics.get("roe"), [m.get("roe") for m in peers], higher_is_better=True)
        div = self._percentile(metrics.get("dividend_yield"),
                               [m.get("dividend_yield") for m in peers], higher_is_better=True)
        components = {"per": per, "pbr": pbr, "roe": roe, "dividend_yield": div}

        def _mean(items):
            vals = [x for x in items if x is not None]
            return round(sum(vals) / len(vals)) if vals else None

        return {
            "score": _mean([per, pbr, roe, div]),
            "valuation_score": _mean([per, pbr]),
            "components": components,
            "peer_count": len(peers),
        }

    @staticmethod
    def _verdict_from_score(valuation_score) -> str:
        # 밸류에이션 순위비율(0~100, 50=업종 중위)로 판정.
        if valuation_score is None:
            return "중립"
        if valuation_score >= 60:
            return "저평가"
        if valuation_score <= 40:
            return "고평가"
        return "중립"

    def analyze(self, code: str) -> dict:
        metrics = self.get_financial_metrics(code)
        if not metrics:
            return None

        # 조회 종목의 업종을 파악해 동일업종 종목으로 업계 평균·순위비율을 낸다.
        # 업종/peer 조회 실패 시 폴백 없이 "조회 실패"로 표시한다.
        industry = self.krx.get_industry(code)
        peers = [c for c in self.krx.get_industry_peers(industry.get("no")) if c != code]
        peer_metrics = self._collect_peer_metrics(peers)  # 중앙값·순위비율 공용(1회 조회)
        industry_avg = self._industry_average(peer_metrics)
        industry_ok = bool(industry.get("name")) and industry_avg.get("peer_count", 0) > 0
        valuation = self.score_valuation(metrics, peer_metrics) if industry_ok else None
        verdict = self._verdict_from_score(valuation["valuation_score"]) if valuation else "조회 실패"

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
            "valuation": valuation,
            "verdict": verdict,
        }
