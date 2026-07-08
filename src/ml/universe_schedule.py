"""ML 신호 파이프라인 D2: 시점별 리밸런싱 유니버스 멤버십.

유니버스를 리밸런스 일자마다 재선정하고, 각 봉(code, date)이 '그 시점' 유효
유니버스에 속할 때만 학습/검증에 쓴다. 이렇게 하면 미래에 유동해진 종목이 과거로
새지 않고(미래참조 차단), 시점별 편입/탈락이 반영된다(생존편향 완화의 첫걸음).

pykrx를 import하지 않는 순수 로직 모듈 — 리밸런스별 종목 목록은 호출자가 넘긴다.
"""
import bisect

import pandas as pd


def _norm(d) -> str:
    """날짜를 'YYYYMMDD' 문자열로 정규화한다."""
    if hasattr(d, "strftime"):
        return d.strftime("%Y%m%d")
    return str(d).replace("-", "")[:8]


def active_universe(rebalances: dict, date) -> list:
    """date 시점에 유효한 유니버스 = date 이하 최근 리밸런스의 종목들. 이전이면 []."""
    keys = sorted(_norm(k) for k in rebalances.keys())
    norm_map = {_norm(k): v for k, v in rebalances.items()}
    target = _norm(date)
    pos = bisect.bisect_right(keys, target) - 1  # target 이하 최근 리밸런스
    if pos < 0:
        return []
    return norm_map[keys[pos]]


def filter_panel_to_universe(panel: pd.DataFrame, rebalances: dict) -> pd.DataFrame:
    """panel의 각 행(code, date)을 그 시점 유효 유니버스 멤버십으로 필터한다."""
    keys = sorted(_norm(k) for k in rebalances.keys())
    norm_map = {_norm(k): set(v) for k, v in rebalances.items()}

    def _member(row) -> bool:
        target = _norm(row["date"])
        pos = bisect.bisect_right(keys, target) - 1
        if pos < 0:
            return False
        return row["code"] in norm_map[keys[pos]]

    mask = panel.apply(_member, axis=1)
    return panel[mask].reset_index(drop=True)
