"""T06 백테스트 평가기 테스트: 손익 계산·기준선 비교·성공 판정 로직 (고정 입력)."""

import numpy as np
import pandas as pd
import pytest

from src.ml.backtest import backtest_fold, evaluate, WARN_SURVIVORSHIP, WARN_NTRIALS
from src.ml.labels import make_returns


def test_backtest_fold_top_k_selection_and_net():
    # prob 상위 2개(0.9, 0.8 → gross_ret 0.10, 0.06)만 매매
    trades = pd.DataFrame({
        "prob": [0.9, 0.8, 0.2, 0.1],
        "gross_ret": [0.10, 0.06, -0.02, -0.05],
    })
    r = backtest_fold(trades, top_k=2, cost=0.01)
    assert r["n_selected"] == 2
    assert r["n_total"] == 4
    # 전략: mean(0.10, 0.06) - 0.01 = 0.07
    assert r["strategy_net"] == pytest.approx(0.07)
    # 바보: mean(0.10,0.06,-0.02,-0.05) - 0.01 = 0.0225 - 0.01 = 0.0125
    assert r["dumb_net"] == pytest.approx(0.0125)


def test_backtest_fold_drops_nan():
    trades = pd.DataFrame({
        "prob": [0.9, np.nan, 0.5],
        "gross_ret": [0.10, 0.20, np.nan],
    })
    r = backtest_fold(trades, top_k=5, cost=0.0)
    assert r["n_total"] == 1  # NaN 행 2개 제외
    assert r["strategy_net"] == pytest.approx(0.10)


def test_backtest_fold_empty():
    trades = pd.DataFrame({"prob": [np.nan], "gross_ret": [np.nan]})
    r = backtest_fold(trades, top_k=3)
    assert r["n_total"] == 0
    assert np.isnan(r["strategy_net"])


def test_evaluate_fold_beats_only_with_margin():
    cost = 0.01  # margin = 2*cost = 0.02
    folds = [
        # 두 기준선을 0.02 마진 이상 상회 → 승리
        {"strategy_net": 0.10, "dumb_net": 0.05, "index_ret": 0.06},
        # 바보전략 대비 마진 부족(0.051 vs 0.05+0.02) → 패배
        {"strategy_net": 0.051, "dumb_net": 0.05, "index_ret": 0.00},
        # 지수 대비 마진 부족 → 패배
        {"strategy_net": 0.10, "dumb_net": 0.00, "index_ret": 0.09},
    ]
    res = evaluate(folds, cost=cost)
    assert [d["beat"] for d in res["details"]] == [True, False, False]


def test_evaluate_success_requires_majority():
    cost = 0.0
    beat = {"strategy_net": 1.0, "dumb_net": 0.0, "index_ret": 0.0}
    lose = {"strategy_net": -1.0, "dumb_net": 0.0, "index_ret": 0.0}

    # 3개 중 2개 승리 → 성공
    res2 = evaluate([beat, beat, lose], cost=cost)
    assert res2["success"] is True
    assert res2["n_beat"] == 2 and res2["required_to_pass"] == 2

    # 3개 중 1개 승리 → 실패 (한 폴드만 좋으면 운)
    res1 = evaluate([beat, lose, lose], cost=cost)
    assert res1["success"] is False


def test_evaluate_reports_warnings_and_ntrials():
    res = evaluate([{"strategy_net": 1.0, "dumb_net": 0.0, "index_ret": 0.0}],
                   n_trials=37)
    assert res["n_trials"] == 37
    assert WARN_SURVIVORSHIP in res["warnings"]
    assert WARN_NTRIALS in res["warnings"]


def test_gross_ret_shares_make_returns_source():
    # 백테스트 입력 gross_ret이 T02와 동일한 시뮬레이션(make_returns)에서 나옴을 확인
    n = 30
    close = 100.0 + np.arange(n)  # 매일 +1 상승
    ohlcv = pd.DataFrame({
        "date": [f"2023{i:04d}" for i in range(n)],
        "open": close, "high": close * 1.01, "low": close * 0.999,
        "close": close, "volume": 1000,
    })
    gross = make_returns(ohlcv, horizon=5)
    trades = pd.DataFrame({"prob": np.linspace(0, 1, n), "gross_ret": gross.values})
    r = backtest_fold(trades.dropna(), top_k=5, cost=0.0)
    # 상승장이라 상위 신호 순수익 > 0
    assert r["strategy_net"] > 0
    assert r["n_total"] == n - 5  # 꼬리 5행은 NaN 제외
