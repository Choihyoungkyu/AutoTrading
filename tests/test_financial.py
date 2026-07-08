import pytest
from unittest.mock import patch, MagicMock
from src.analyzers.financial_analyzer import FinancialAnalyzer


@pytest.fixture
def mock_krx():
    krx = MagicMock()
    return krx


@pytest.fixture
def analyzer(mock_krx):
    return FinancialAnalyzer(mock_krx)


# 업종 peer 3개사 — 순위비율(percentile) 판정용.
# PER/PBR/ROE/배당: 아래 값들과 대상 종목을 비교해 상대 순위를 매긴다.
PEERS = [
    {"per": 14.0, "pbr": 1.6, "roe": 10.0, "dividend_yield": 1.2},
    {"per": 15.0, "pbr": 1.8, "roe": 12.0, "dividend_yield": 1.5},
    {"per": 20.0, "pbr": 2.4, "roe": 8.0, "dividend_yield": 0.9},
]


def _analyze_with_peers(analyzer, peers=PEERS):
    # 업종 조회는 성공했다고 보고(peer_count>0), peer 지표만 주입한다.
    analyzer.krx.get_industry.return_value = {"no": "1", "name": "반도체"}
    analyzer.krx.get_industry_peers.return_value = ["p1", "p2", "p3"]
    with patch.object(analyzer, "_collect_peer_metrics", return_value=peers):
        return analyzer.analyze("005930")


def test_verdict_undervalued(analyzer, mock_krx):
    # PER 8·PBR 1.0 → 모든 peer보다 낮음 → 밸류에이션 순위비율 최상위 → 저평가
    mock_krx.get_market_cap.return_value = {
        "per": 8.0, "pbr": 1.0, "eps": 3500, "bps": 50000, "dividend_yield": 2.1,
    }
    result = _analyze_with_peers(analyzer)
    assert result["verdict"] == "저평가"
    assert result["valuation"]["valuation_score"] == 100


def test_verdict_overvalued(analyzer, mock_krx):
    # PER 25·PBR 3.0 → 모든 peer보다 높음 → 밸류에이션 순위비율 최하위 → 고평가
    mock_krx.get_market_cap.return_value = {
        "per": 25.0, "pbr": 3.0, "eps": 3500, "bps": 50000, "dividend_yield": 2.1,
    }
    result = _analyze_with_peers(analyzer)
    assert result["verdict"] == "고평가"
    assert result["valuation"]["valuation_score"] == 0


def test_verdict_neutral(analyzer, mock_krx):
    # PER 15·PBR 1.8 → 업종 중위권 → 순위비율 ~50 → 중립
    mock_krx.get_market_cap.return_value = {
        "per": 15.0, "pbr": 1.8, "eps": 3500, "bps": 50000, "dividend_yield": 2.1,
    }
    result = _analyze_with_peers(analyzer)
    assert result["verdict"] == "중립"


def test_percentile_helper():
    # 낮을수록 우수(PER): 대상이 3개 중 2개보다 낮으면 상위 67점
    assert FinancialAnalyzer._percentile(10, [12, 15, 8], higher_is_better=False) == 67
    # 높을수록 우수(ROE): 대상이 3개 중 2개보다 높으면 상위 67점
    assert FinancialAnalyzer._percentile(11, [10, 8, 12], higher_is_better=True) == 67
    # 비교 대상 없음 → None
    assert FinancialAnalyzer._percentile(10, [], higher_is_better=False) is None


def test_analyze_response_keys(analyzer, mock_krx):
    mock_krx.get_market_cap.return_value = {
        "per": 8.5,
        "pbr": 1.2,
        "eps": 3500,
        "bps": 50000,
        "dividend_yield": 2.1,
    }

    result = _analyze_with_peers(analyzer)
    assert "code" in result
    assert "per" in result
    assert "pbr" in result
    assert "roe" in result
    assert "eps" in result
    assert "bps" in result
    assert "debt_ratio" in result
    assert "dividend_yield" in result
    assert "industry_avg" in result
    assert "valuation" in result
    assert "verdict" in result


def test_analyze_endpoint():
    from main import create_app

    app = create_app()
    client = app.test_client()

    with patch("src.api.routes.financial_analyzer.analyze") as mock_analyze:
        mock_analyze.return_value = {
            "code": "005930",
            "per": 8.5,
            "pbr": 1.2,
            "roe": 7.0,
            "eps": 3500,
            "bps": 50000,
            "debt_ratio": 45.2,
            "dividend_yield": 2.1,
            "industry_avg": {
                "per": 15.0,
                "pbr": 1.8,
                "roe": 12.0,
                "dividend_yield": 1.5,
            },
            "verdict": "저평가",
        }

        response = client.get("/analyze/005930/financial")
        assert response.status_code == 200
        data = response.get_json()
        assert data["code"] == "005930"
        assert data["verdict"] == "저평가"
