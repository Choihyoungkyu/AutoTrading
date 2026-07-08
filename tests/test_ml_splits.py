import pandas as pd

from src.ml.splits import make_folds


def _dates():
    # 2022~2024 합성 거래일(월별 1일, 오름차순). 네트워크 불필요.
    return [
        f"{y}{m:02d}01"
        for y in (2022, 2023, 2024)
        for m in range(1, 13)
    ]


def _gap_trading_days(dates, train_end, val_start):
    # dates(정렬)에서 train_end 다음부터 val_start 직전까지의 거래일 수.
    idx = {d: i for i, d in enumerate(dates)}
    return idx[val_start] - idx[train_end] - 1


def test_검증이_학습보다_항상_미래():
    dates = _dates()
    folds = [("20230101", "20231201"), ("20240101", "20241201")]
    result = make_folds(dates, folds, embargo=5)
    assert len(result) == 2
    for fold in result:
        assert fold["train"][1] < fold["val"][0]  # 학습 끝 < 검증 시작


def test_embargo_갭이_정확히_이상():
    dates = _dates()
    embargo = 5
    folds = [("20230601", "20231201")]
    result = make_folds(dates, folds, embargo=embargo)
    fold = result[0]
    gap = _gap_trading_days(dates, fold["train"][1], fold["val"][0])
    assert gap >= embargo
    assert gap == embargo  # 학습 끝을 정확히 embargo 갭만큼 당긴다


def test_기본_embargo는_5():
    dates = _dates()
    folds = [("20230601", "20231201")]
    result = make_folds(dates, folds)  # embargo 생략 → 5
    fold = result[0]
    assert _gap_trading_days(dates, fold["train"][1], fold["val"][0]) == 5


def test_반환_구조_계약():
    dates = _dates()
    folds = [("20230101", "20231201")]
    result = make_folds(dates, folds)
    fold = result[0]
    assert set(fold.keys()) == {"train", "val", "is_lockbox"}
    assert isinstance(fold["train"], tuple) and len(fold["train"]) == 2
    assert isinstance(fold["val"], tuple) and len(fold["val"]) == 2
    assert isinstance(fold["is_lockbox"], bool)


def test_여러_시기_walkforward():
    dates = _dates()
    folds = [
        ("20220801", "20221201"),
        ("20230101", "20231201"),
        ("20240101", "20241201"),
    ]
    result = make_folds(dates, folds, embargo=5)
    assert len(result) == 3
    # 시간 순서가 유지되어야 한다(무작위 셔플 금지).
    val_starts = [f["val"][0] for f in result]
    assert val_starts == sorted(val_starts)


def test_lockbox가_일반폴드에_포함안됨():
    dates = _dates()
    folds = [
        ("20230101", "20231201"),
        ("20240101", "20241201"),  # 이 구간이 lockbox와 겹침
    ]
    result = make_folds(dates, folds, embargo=5, lockbox=("20240101", "20241201"))
    normal = [f for f in result if not f["is_lockbox"]]
    locked = [f for f in result if f["is_lockbox"]]

    assert len(normal) == 1
    assert normal[0]["val"] == ("20230101", "20231201")

    assert len(locked) == 1
    assert locked[0]["val"] == ("20240101", "20241201")
    # 봉인 구간도 검증은 학습보다 미래여야 한다.
    assert locked[0]["train"][1] < locked[0]["val"][0]


def test_pandas_입력_지원():
    # DatetimeIndex 입력도 정규화되어야 한다.
    dates = pd.to_datetime(_dates(), format="%Y%m%d")
    folds = [(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-01"))]
    result = make_folds(dates, folds, embargo=5)
    assert result[0]["val"] == ("20230101", "20231201")
    assert result[0]["train"][1] < result[0]["val"][0]


def test_학습부족_폴드는_제외():
    dates = _dates()
    # 첫 거래일이 검증 시작이면 embargo 갭 확보 불가 → 제외.
    folds = [("20220101", "20220601")]
    result = make_folds(dates, folds, embargo=5)
    assert result == []
