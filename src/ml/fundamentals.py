"""ML 신호 파이프라인 C1: 재무 피처의 인과적(as-of) 조인 — 순수 로직.

특정 시점 t의 재무 피처는 t 이하 '이미 공시된' 최근 값만 써야 한다. pd.merge_asof
(direction=backward)로 각 OHLCV 봉에 그 날짜 이하 최근 공시값을 붙인다. 미래 공시가
과거 봉에 새는 미래참조를 원천 차단하고, 첫 공시 이전 봉은 NaN으로 남긴다.

pykrx를 import하지 않는 순수 모듈 — 재무 데이터는 호출자가 DataFrame으로 넘긴다.
"""
import pandas as pd


def join_fundamentals_asof(ohlcv: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.DataFrame:
    """ohlcv 각 행(date d)에 d 이하 최근 공시 재무값을 붙인 DataFrame(길이 N)을 반환한다.

    - ohlcv: 컬럼 date(YYYYMMDD str)를 포함, 길이 N.
    - fundamentals: 컬럼 date(YYYYMMDD str) + 재무값 컬럼들.
    - 반환: 재무값 컬럼들만, ohlcv 순서·길이 유지. 첫 공시 이전 행은 NaN.
    """
    value_cols = [c for c in fundamentals.columns if c != "date"]

    def _to_key(s):  # "20210105"·"2021-01-05" 모두 YYYYMMDD로 정규화 후 파싱(무모호)
        norm = s.astype(str).str.replace("-", "", regex=False).str.slice(0, 8)
        return pd.to_datetime(norm, format="%Y%m%d")

    left = pd.DataFrame({
        "_key": _to_key(ohlcv["date"]),
        "_pos": range(len(ohlcv)),
    })
    right = fundamentals.copy()
    right["_key"] = _to_key(right["date"])
    right = right[["_key"] + value_cols].sort_values("_key")

    # left는 정렬 후 merge하고 원래 순서로 되돌린다(merge_asof는 정렬 입력 요구).
    left_sorted = left.sort_values("_key")
    merged = pd.merge_asof(left_sorted, right, on="_key", direction="backward")
    merged = merged.sort_values("_pos")
    return merged[value_cols].reset_index(drop=True)
