from src.collectors.krx_collector import KRXCollector
from src.collectors.yfinance_collector import YFinanceCollector

SEMICONDUCTOR_PEERS = ["000660", "000990", "036930", "240810"]


class FinancialAnalyzer:
    def __init__(self, krx_collector: KRXCollector, yfinance_collector: YFinanceCollector = None):
        self.krx = krx_collector
        self.yf = yfinance_collector or YFinanceCollector()

    def get_financial_metrics(self, code: str, date: str = None) -> dict:
        metrics = self.krx.get_market_cap(code, date)
        if not metrics:
            return None

        eps = metrics.get("eps", 0)
        bps = metrics.get("bps", 0)
        roe = (eps / bps * 100) if bps > 0 else 0

        debt_ratio = 0
        try:
            import yfinance
            ticker = yfinance.Ticker(f"{code}.KS")
            debt_to_equity = ticker.info.get("debtToEquity", 0)
            debt_ratio = float(debt_to_equity) if debt_to_equity else 0
        except Exception:
            pass

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

    def get_industry_average(self, peer_codes: list = None) -> dict:
        if peer_codes is None:
            peer_codes = SEMICONDUCTOR_PEERS

        per_values = []
        pbr_values = []
        roe_values = []
        dividend_values = []

        for peer_code in peer_codes:
            try:
                metrics = self.get_financial_metrics(peer_code)
                if metrics:
                    if metrics.get("per", 0) > 0:
                        per_values.append(metrics["per"])
                    if metrics.get("pbr", 0) > 0:
                        pbr_values.append(metrics["pbr"])
                    if metrics.get("roe", 0) > 0:
                        roe_values.append(metrics["roe"])
                    if metrics.get("dividend_yield", 0) > 0:
                        dividend_values.append(metrics["dividend_yield"])
            except Exception:
                continue

        return {
            "per": sum(per_values) / len(per_values) if per_values else 0,
            "pbr": sum(pbr_values) / len(pbr_values) if pbr_values else 0,
            "roe": sum(roe_values) / len(roe_values) if roe_values else 0,
            "dividend_yield": sum(dividend_values) / len(dividend_values) if dividend_values else 0,
            "peer_count": len(per_values),
        }

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

        industry_avg = self.get_industry_average()
        verdict = self.determine_verdict(metrics, industry_avg)

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
            "industry_avg": {
                "per": round(industry_avg["per"], 2),
                "pbr": round(industry_avg["pbr"], 2),
                "roe": round(industry_avg["roe"], 2),
                "dividend_yield": round(industry_avg["dividend_yield"], 2),
            },
            "verdict": verdict,
        }
