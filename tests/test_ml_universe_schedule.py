"""D2: 시점별 리밸런싱 유니버스 멤버십 테스트.

각 과거 시점에 그 시점 유동성 상위 종목만 쓰도록 한다. 미래에 유동해진 종목이
과거 폴드에 새어들거나(미래참조), 특정 시점에 부활한 종목이 그 이전 구간에
소급 편입되면 안 된다.
"""
import pandas as pd

from src.ml.universe_schedule import active_universe, filter_panel_to_universe


REBALANCES = {
    "20210101": ["A", "B"],
    "20210401": ["B", "C"],  # A 탈락, C 진입
}


def test_active_universe_returns_latest_rebalance_on_or_before_date():
    assert active_universe(REBALANCES, "20210215") == ["A", "B"]
    assert active_universe(REBALANCES, "20210501") == ["B", "C"]


def test_active_universe_exact_boundary_uses_that_rebalance():
    assert active_universe(REBALANCES, "20210401") == ["B", "C"]


def test_active_universe_before_first_rebalance_is_empty():
    assert active_universe(REBALANCES, "20201231") == []


def test_filter_panel_keeps_only_active_members():
    panel = pd.DataFrame({
        "date": ["20210215", "20210215", "20210501", "20210501"],
        "code": ["A", "B", "A", "C"],
        "close": [1.0, 2.0, 3.0, 4.0],
    })
    out = filter_panel_to_universe(panel, REBALANCES)
    # 20210215: A,B 유효 → 둘 다 유지. 20210501: B,C 유효 → A 탈락, C 유지.
    assert list(zip(out["date"], out["code"])) == [
        ("20210215", "A"), ("20210215", "B"), ("20210501", "C")
    ]


def test_filter_panel_drops_rows_before_first_rebalance():
    panel = pd.DataFrame({
        "date": ["20201231", "20210215"],
        "code": ["A", "A"],
        "close": [1.0, 2.0],
    })
    out = filter_panel_to_universe(panel, REBALANCES)
    assert out["date"].tolist() == ["20210215"]
