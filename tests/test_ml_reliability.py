"""D3: 신뢰성 리포트 테스트 — 폴드 안정성 + deflated Sharpe 보정.

'엣지 없음'이든 '엣지 있음'이든 그 결론을 믿을 수 있는지 재는 지표. 폴드 전반의
일관성(부호 안정성·분산)과 시도 횟수(n_trials) 보정을 함께 본다.
"""
import math

from src.ml.reliability import reliability_report


def _fold(s, d, i):
    return {"strategy_net": s, "dumb_net": d, "index_ret": i}


def test_stable_positive_edge_has_consistent_sign():
    folds = [_fold(0.02, 0.0, 0.005), _fold(0.03, 0.0, 0.004),
             _fold(0.025, 0.0, 0.006), _fold(0.028, 0.0, 0.005)]
    r = reliability_report(folds, n_trials=1)
    assert r["n_folds"] == 4
    assert r["n_positive_excess"] == 4          # 모든 폴드에서 기준선 상회
    assert r["strategy_net_mean"] > 0
    assert r["sharpe_across_folds"] > 0


def test_mixed_edge_is_not_sign_consistent():
    folds = [_fold(0.05, 0.0, 0.0), _fold(-0.04, 0.0, 0.0),
             _fold(0.03, 0.0, 0.0), _fold(-0.02, 0.0, 0.0)]
    r = reliability_report(folds, n_trials=1)
    assert r["n_positive_excess"] == 2          # 절반만 상회 → 불안정
    assert r["strategy_net_spread"] > 0.08      # 큰 편차


def test_deflated_sharpe_threshold_grows_with_trials():
    folds = [_fold(0.02, 0.0, 0.0), _fold(0.03, 0.0, 0.0), _fold(0.025, 0.0, 0.0)]
    assert reliability_report(folds, n_trials=1)["deflated_sharpe_threshold"] == 0.0
    r100 = reliability_report(folds, n_trials=100)
    assert abs(r100["deflated_sharpe_threshold"] - math.sqrt(2 * math.log(100))) < 1e-9


def test_deflated_sharpe_pass_requires_beating_null_max():
    # n_trials가 크면 관측 Sharpe가 우연의 최대 기대치를 넘어야만 통과.
    folds = [_fold(0.02, 0.0, 0.0), _fold(-0.01, 0.0, 0.0), _fold(0.03, 0.0, 0.0)]
    assert reliability_report(folds, n_trials=1)["passes_deflated_sharpe"] is True
    assert reliability_report(folds, n_trials=1000)["passes_deflated_sharpe"] is False


def test_report_includes_eval_and_warnings():
    folds = [_fold(0.02, 0.0, 0.0), _fold(0.03, 0.0, 0.0)]
    r = reliability_report(folds, n_trials=1)
    assert "success" in r["eval"]
    assert any("생존 편향" in w for w in r["warnings"])
