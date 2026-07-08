"""ML 신호 파이프라인 D1: point-in-time 포워드 분할조정.

수정주가의 함정: pykrx 기본 수정주가(adjusted=True)는 '오늘' 기준으로 과거를 소급
조정해 미래참조 누수를 만든다(미래 분할이 과거 봉을 바꿈). 원본가는 분할일에 가짜
가격 점프가 생겨 라벨=돈 불변식을 깨뜨린다.

포워드 조정은 분할 이벤트를 '관측 시점 이후'로만 적용한다: 분할일 이전 봉은 절대
바뀌지 않고(누수 없음), 분할일부터 누적계수를 곱해 점프를 제거한다(연속성).
"""
import pandas as pd

_PRICE_COLS = ["open", "high", "low", "close"]


def adjust_ohlcv(ohlcv: pd.DataFrame, splits: list) -> pd.DataFrame:
    """원본 OHLCV를 point-in-time 포워드 분할조정한다.

    splits: [(date, ratio)] — date는 ohlcv["date"]와 같은 형식의 분할 적용일,
    ratio는 주식수 배수(2:1 분할=2.0, 1:10 병합=0.1). 분할일 이전 봉은 불변.
    """
    out = ohlcv.copy()
    if not splits:
        return out

    # 각 봉의 누적계수 cf = (그 날짜 <= 봉날짜인 분할들의 ratio 곱). 분할 전이면 1.
    cf = pd.Series(1.0, index=out.index)
    for split_date, ratio in splits:
        cf = cf.where(out["date"].astype(str) < str(split_date), cf * ratio)

    for col in _PRICE_COLS:
        out[col] = out[col].astype(float) * cf
    out["volume"] = out["volume"].astype(float) / cf  # 주식수 기준 일관성
    return out


def derive_splits(raw: pd.DataFrame, adjusted: pd.DataFrame) -> list:
    """pykrx 원본가·back-adjusted 시세를 비교해 분할 이벤트 [(date, ratio)]를 복원한다.

    분할 일자·배수는 공개된 과거 사실이므로, 이를 추출해 원본가에 포워드 적용하면
    (adjust_ohlcv) 미래참조 없이 점프를 제거할 수 있다. back-adjusted 계수는 과거로
    갈수록 커지고 분할일마다 계단식으로 변하며, 그 비율이 곧 배수다.
    """
    factor = (raw["close"].astype(float) / adjusted["close"].astype(float)).round(6)
    dates = raw["date"].astype(str).tolist()
    fvals = factor.tolist()
    splits = []
    for t in range(1, len(fvals)):
        if fvals[t] != fvals[t - 1] and fvals[t] != 0:
            splits.append((dates[t], round(fvals[t - 1] / fvals[t], 6)))
    return splits
