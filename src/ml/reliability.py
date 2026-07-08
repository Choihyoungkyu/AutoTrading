"""ML 신호 파이프라인 D3: 신뢰성 리포트 (폴드 안정성 + deflated Sharpe 보정).

'엣지 있음/없음' 결론을 믿을 수 있는지 재는 계층. evaluate()의 승패 판정 위에
(1) 폴드 전반 일관성(기준선 초과의 부호 안정성·분산)과 (2) 시도 횟수(n_trials)
보정을 더한다. 폴드 수가 적으면 Sharpe 추정이 약하므로 리포트 해석 시 주의한다.
"""
import math
import statistics

from src.ml.backtest import evaluate, WARN_SURVIVORSHIP, WARN_NTRIALS


def reliability_report(fold_metrics: list, n_trials: int = 1,
                       cost: float = 0.007, margin_mult: float = 2.0) -> dict:
    """폴드 성과의 안정성과 과최적화 보정 지표를 담은 신뢰성 리포트를 반환한다."""
    nets = [f["strategy_net"] for f in fold_metrics]
    n = len(nets)
    mean = statistics.fmean(nets) if n else float("nan")
    std = statistics.stdev(nets) if n >= 2 else 0.0

    # 각 폴드에서 '더 나은 기준선'(다 사기·지수 중 큰 값) 대비 초과수익의 부호 안정성.
    excess = [f["strategy_net"] - max(f["dumb_net"], f["index_ret"]) for f in fold_metrics]
    n_positive_excess = sum(1 for e in excess if e > 0)

    # 폴드 간 Sharpe(표본 표준편차 기준). 관측치가 적어 추정이 약함 — 리포트에서 유의.
    if n >= 2 and std > 0:
        sharpe = mean / std
    elif n >= 2:  # std == 0 (모든 폴드 동일)
        sharpe = math.inf if mean > 0 else (-math.inf if mean < 0 else 0.0)
    else:
        sharpe = None

    # deflated Sharpe 임계치: N회 시도 시 백색잡음 Sharpe 최대 기대치 ≈ sqrt(2 ln N).
    # 관측 Sharpe가 이 우연의 기대치를 넘지 못하면 '성공'을 신뢰하지 않는다.
    threshold = math.sqrt(2 * math.log(n_trials)) if n_trials > 1 else 0.0
    passes = sharpe is not None and sharpe > threshold

    return {
        "n_folds": n,
        "strategy_net_mean": mean,
        "strategy_net_std": std,
        "strategy_net_min": min(nets) if nets else float("nan"),
        "strategy_net_max": max(nets) if nets else float("nan"),
        "strategy_net_spread": (max(nets) - min(nets)) if nets else float("nan"),
        "excess_over_best_baseline": excess,
        "n_positive_excess": n_positive_excess,
        "sharpe_across_folds": sharpe,
        "deflated_sharpe_threshold": threshold,
        "passes_deflated_sharpe": bool(passes),
        "eval": evaluate(fold_metrics, cost=cost, margin_mult=margin_mult, n_trials=n_trials),
        "warnings": [WARN_SURVIVORSHIP, WARN_NTRIALS],
    }
