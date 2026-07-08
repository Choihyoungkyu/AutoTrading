import pandas as pd


def make_returns(
    ohlcv, stop_loss: float = -0.03, horizon: int = 5
) -> "pd.Series":
    """각 행 T의 경로 의존 실현손익(비율, 비용 전)을 반환한다. 미래 horizon일이 없는 꼬리 행은 NaN.

    이 함수가 매매 시뮬레이션의 단일 출처다. 라벨(make_labels)과 백테스트(T06)는
    반드시 이 실현손익을 공유해야 "라벨 = 실제로 번 돈" 불변식이 깨지지 않는다.
    """
    n = len(ohlcv)
    close = ohlcv["close"].to_numpy(dtype=float)
    low = ohlcv["low"].to_numpy(dtype=float)

    rets = [float("nan")] * n
    for t in range(n):
        # 미래 horizon일이 부족한 꼬리 행은 실현손익 계산 불가.
        if t + horizon >= n:
            continue

        entry = close[t]
        stop_price = entry * (1.0 + stop_loss)

        # T+1 ~ T+horizon 경로를 따라가며 손절 터치를 먼저 확인한다.
        pnl = None
        for h in range(1, horizon + 1):
            if low[t + h] <= stop_price:
                pnl = stop_loss  # 손절가 청산: 실현손익은 stop_loss.
                break

        # 손절 미발동이면 T+horizon 종가로 청산한다.
        if pnl is None:
            pnl = close[t + horizon] / entry - 1.0

        rets[t] = pnl

    return pd.Series(rets, index=ohlcv.index)


def make_labels(
    ohlcv, stop_loss: float = -0.03, horizon: int = 5, cost: float = 0.007
) -> "pd.Series":
    """각 행 T에 대해 실제 매매 규칙의 경로 의존 실현손익으로 0/1 라벨을 만든다. 미래 horizon일이 없는 꼬리 행은 NaN."""
    rets = make_returns(ohlcv, stop_loss=stop_loss, horizon=horizon)
    # 비용을 초과한 (+) 실현손익만 매수 정답(1). 꼬리 행(NaN)은 라벨도 NaN.
    labels = rets.apply(lambda pnl: pnl if pd.isna(pnl) else (1.0 if (pnl - cost) > 0 else 0.0))
    return labels
