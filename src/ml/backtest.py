"""T06: 백테스트 평가기 + 성공 판정.

확률 상위 신호만 매매한 전략의 '비용 제외' 성과를 두 기준선과 비교해 성공/실패를 판정한다.
지표는 전체 정확도가 아니라 '실제로 거래할 상위 신호의 순수익'이다.

성과의 실현손익(gross_ret)은 반드시 labels.make_returns와 동일한 매매 시뮬레이션에서
나와야 한다 (라벨=돈 불변식). 이 모듈은 그 gross_ret을 입력으로 받는다.
"""

import math
import pandas as pd

# 조사 리포트(과최적화·백테스트 위험) + PRD 한계를 결과에 항상 동봉하는 경고
WARN_SURVIVORSHIP = "생존 편향: 상폐·거래정지 종목 미포함으로 성능이 낙관적으로 나옴."
WARN_NTRIALS = (
    "과최적화 경고: 시도 횟수(n_trials)가 많을수록 우연한 성공 확률이 커진다. "
    "n_trials를 보고하고 deflated Sharpe 등으로 보정하지 않은 성공은 신뢰하지 말 것."
)


def backtest_fold(trades: pd.DataFrame, top_k: int, cost: float = 0.007) -> dict:
    """한 폴드에서 확률 상위 top_k만 매매한 전략과 '다 사는' 기준선의 비용 제외 평균 순수익을 계산한다.

    trades: 컬럼 'prob'(모델 매수 확률), 'gross_ret'(실현손익 비율, 비용 전).
    지표는 트레이드당 평균 순수익(= 평균 gross_ret - cost)으로 폴드 간 비교 가능하게 한다.
    """
    clean = trades.dropna(subset=["prob", "gross_ret"])
    if clean.empty:
        return {"strategy_net": float("nan"), "dumb_net": float("nan"),
                "n_selected": 0, "n_total": 0}

    selected = clean.sort_values("prob", ascending=False).head(top_k)
    strategy_net = float(selected["gross_ret"].mean() - cost)
    dumb_net = float(clean["gross_ret"].mean() - cost)  # 다 사서 5일 청산
    return {
        "strategy_net": strategy_net,
        "dumb_net": dumb_net,
        "n_selected": int(len(selected)),
        "n_total": int(len(clean)),
    }


def evaluate(folds: list, cost: float = 0.007, margin_mult: float = 2.0,
             n_trials: int = 1) -> dict:
    """walk-forward 폴드들의 성과로 성공/실패를 판정한다.

    각 fold dict는 strategy_net, dumb_net, index_ret(코스피 지수 보유 수익)을 가진다.
    한 폴드 '승리' 조건: 전략 순수익이 두 기준선(바보 전략·지수)을 모두
    거래비용의 margin_mult배 마진으로 상회. 성공: 폴드 과반수에서 승리.
    """
    margin = margin_mult * cost
    details = []
    n_beat = 0
    for i, f in enumerate(folds):
        beats_dumb = f["strategy_net"] > f["dumb_net"] + margin
        beats_index = f["strategy_net"] > f["index_ret"] + margin
        beat = bool(beats_dumb and beats_index)
        n_beat += int(beat)
        details.append({
            "fold": i,
            "strategy_net": f["strategy_net"],
            "dumb_net": f["dumb_net"],
            "index_ret": f["index_ret"],
            "beats_dumb": bool(beats_dumb),
            "beats_index": bool(beats_index),
            "beat": beat,
        })

    n_folds = len(folds)
    # 과반수(strict majority): 3개 중 2개↑. 한 폴드만 좋으면 운으로 간주해 실패.
    success = n_folds > 0 and n_beat > n_folds / 2

    return {
        "success": success,
        "n_folds": n_folds,
        "n_beat": n_beat,
        "required_to_pass": math.floor(n_folds / 2) + 1 if n_folds else 0,
        "margin": margin,
        "n_trials": n_trials,
        "details": details,
        "warnings": [WARN_SURVIVORSHIP, WARN_NTRIALS],
    }
