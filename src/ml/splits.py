"""시간순 walk-forward 학습/검증 분할기 (embargo 갭 + lockbox 봉인)."""

from typing import Optional


def _to_key_list(dates) -> list[str]:
    """정렬된 거래일(str/pandas)을 비교 가능한 'YYYYMMDD' 문자열 리스트로 정규화한다."""
    keys: list[str] = []
    for d in list(dates):
        if hasattr(d, "strftime"):  # pandas Timestamp / datetime
            keys.append(d.strftime("%Y%m%d"))
        else:
            keys.append(str(d).replace("-", "")[:8])
    return keys


def _to_key(value) -> str:
    """단일 날짜(str/pandas)를 'YYYYMMDD' 문자열로 정규화한다."""
    if hasattr(value, "strftime"):
        return value.strftime("%Y%m%d")
    return str(value).replace("-", "")[:8]


def make_folds(dates, folds, embargo: int = 5, lockbox=None) -> list:
    """시간순 walk-forward 폴드 생성.

    입력 형식:
      - dates: 오름차순 정렬된 거래일. list/Series of str "YYYYMMDD" 또는 pandas
               Timestamp/DatetimeIndex 허용. 내부적으로 "YYYYMMDD"로 정규화한다.
      - folds: 검증 구간 정의 리스트. 각 원소는 (val_start, val_end) 튜플이며
               값은 dates와 같은 형식의 날짜(포함 범위, inclusive). 여러 시기 지정 가능.
      - embargo: 학습 끝과 검증 시작 사이에 비워둘 최소 거래일 수(기본 5).
      - lockbox: 마지막 봉인 구간. (lb_start, lb_end) 튜플 또는 None.

    반환: list[dict]. 각 원소는
      {"train": (start, end), "val": (start, end), "is_lockbox": bool}.
    train/val 경계는 "YYYYMMDD" 문자열. 검증은 항상 학습보다 미래이며, 학습 끝과
    검증 시작 사이 dates 기준 거래일 갭이 정확히 >= embargo 가 되도록 학습 끝을 당긴다.
    """
    keys = _to_key_list(dates)
    index = {k: i for i, k in enumerate(keys)}

    lb_start = lb_end = None
    if lockbox is not None:
        lb_start, lb_end = _to_key(lockbox[0]), _to_key(lockbox[1])

    def _in_lockbox(val_start: str, val_end: str) -> bool:
        # 검증 구간이 lockbox 범위와 겹치면 봉인 폴드로 간주한다.
        if lb_start is None:
            return False
        return not (val_end < lb_start or val_start > lb_end)

    result: list[dict] = []
    for f in folds:
        val_start, val_end = _to_key(f[0]), _to_key(f[1])
        is_lockbox = _in_lockbox(val_start, val_end)

        # 검증 시작 위치보다 embargo 만큼 앞선 거래일을 학습 끝으로 삼는다.
        vs_pos = _first_pos_ge(keys, val_start)
        train_end_pos = vs_pos - embargo - 1
        if train_end_pos < 0:
            # 학습 데이터가 embargo 갭을 확보할 만큼 없으면 해당 폴드는 건너뛴다.
            continue

        train_start = keys[0]
        train_end = keys[train_end_pos]

        result.append(
            {
                "train": (train_start, train_end),
                "val": (val_start, val_end),
                "is_lockbox": is_lockbox,
            }
        )

    return result


def _first_pos_ge(keys: list[str], target: str) -> int:
    """target 이상인 첫 거래일의 인덱스 반환(정확 일치 없으면 다음 거래일)."""
    for i, k in enumerate(keys):
        if k >= target:
            return i
    return len(keys)
