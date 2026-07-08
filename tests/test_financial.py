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


def test_verdict_undervalued(analyzer, mock_krx):
    mock_krx.get_market_cap.return_value = {
        "per": 8.0,
        "pbr": 1.0,
        "eps": 3500,
        "bps": 50000,
        "dividend_yield": 2.1,
    }

    with patch.object(analyzer, "get_industry_average", return_value={
        "per": 15.0,
        "pbr": 1.8,
        "roe": 12.0,
        "dividend_yield": 1.5,
    }):
        result = analyzer.analyze("005930")
        assert result["verdict"] == "저평가"


def test_verdict_overvalued(analyzer, mock_krx):
    mock_krx.get_market_cap.return_value = {
        "per": 25.0,
        "pbr": 3.0,
        "eps": 3500,
        "bps": 50000,
        "dividend_yield": 2.1,
    }

    with patch.object(analyzer, "get_industry_average", return_value={
        "per": 15.0,
        "pbr": 1.8,
        "roe": 12.0,
        "dividend_yield": 1.5,
    }):
        result = analyzer.analyze("005930")
        assert result["verdict"] == "고평가"


def test_verdict_neutral(analyzer, mock_krx):
    mock_krx.get_market_cap.return_value = {
        "per": 8.0,
        "pbr": 3.0,
        "eps": 3500,
        "bps": 50000,
        "dividend_yield": 2.1,
    }

    with patch.object(analyzer, "get_industry_average", return_value={
        "per": 15.0,
        "pbr": 1.8,
        "roe": 12.0,
        "dividend_yield": 1.5,
    }):
        result = analyzer.analyze("005930")
        assert result["verdict"] == "중립"


def test_analyze_response_keys(analyzer, mock_krx):
    mock_krx.get_market_cap.return_value = {
        "per": 8.5,
        "pbr": 1.2,
        "eps": 3500,
        "bps": 50000,
        "dividend_yield": 2.1,
    }

    with patch.object(analyzer, "get_industry_average", return_value={
        "per": 15.0,
        "pbr": 1.8,
        "roe": 12.0,
        "dividend_yield": 1.5,
    }):
        result = analyzer.analyze("005930")
        assert "code" in result
        assert "per" in result
        assert "pbr" in result
        assert "roe" in result
        assert "eps" in result
        assert "bps" in result
        assert "debt_ratio" in result
        assert "dividend_yield" in result
        assert "industry_avg" in result
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
