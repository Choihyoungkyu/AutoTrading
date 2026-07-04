from unittest.mock import patch


def _client():
    from main import create_app
    return create_app().test_client()


def test_search_returns_results():
    results = [
        {"code": "035420", "name": "NAVER", "market": "코스피"},
        {"code": "323990", "name": "박셀바이오", "market": "코스닥"},
    ]
    with patch("src.api.routes.krx.search", return_value=results) as mock_search:
        resp = _client().get("/search?q=naver")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["code"] == "035420"
        assert data[0]["name"] == "NAVER"
        mock_search.assert_called_once_with("naver")


def test_search_empty_query():
    with patch("src.api.routes.krx.search") as mock_search:
        resp = _client().get("/search?q=")
        assert resp.status_code == 200
        assert resp.get_json() == []
        mock_search.assert_not_called()
