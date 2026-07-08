"""ML 신호 파이프라인 C1: 재무 피처 추가가 대형주에서 엣지를 만드는가.

D 베이스라인(차트 16피처, 대형주 유니버스)과의 유일한 차이는 '소수의 재무 피처
추가'다(유니버스·기간·폴드 동일). 공정한 A/B를 위해 START/END/HORIZON/COST/EMBARGO/
TOP_N/FOLDS/LOCKBOX를 run_demo.py와 동일하게 둔다.

미래참조 금지: 재무 피처는 join_fundamentals_asof(merge_asof backward)로 각 봉 날짜
이하 '이미 공시된' 최근 값만 붙인다. pykrx get_market_fundamental은 KRX가 공시 시점에
갱신하므로 사실상 point-in-time이며, as-of 조인이 이를 한 번 더 강제한다.
"""
import sys
from dotenv import load_dotenv
load_dotenv()  # pykrx import 전에 KRX 자격증명 로드

import pandas as pd
from pykrx import stock

from src.ml.pipeline import (
    build_panel, annual_rebalance_dates, evaluate_folds, log,
)
from src.ml.universe import UniverseSelector
from src.ml.universe_schedule import filter_panel_to_universe
from src.ml.reliability import reliability_report
from src.ml.fundamentals import join_fundamentals_asof

# --- D와 동일 설정 ---
START, END = "20190101", "20241231"
HORIZON = 5
COST = 0.007
EMBARGO = 5
TOP_N = 30
FOLDS = [("20200101", "20201231"), ("20210101", "20211231"),
         ("20220101", "20221231"), ("20230101", "20231231"),
         ("20240101", "20241231")]
LOCKBOX = ("20240101", "20241231")

# D의 차트 16피처
CHART_FEATURES = ["ma_5", "ma_20", "ma_50", "ma_60", "rsi_14", "macd_line",
                  "macd_signal", "macd_histogram", "bb_upper", "bb_middle",
                  "bb_lower", "bb_pct_b", "stoch_k", "stoch_d", "obv", "obv_trend"]

# C1이 추가하는 재무 피처 (min-viable 4개: PER, PBR, DIV, 이익수익률=1/PER)
FUND_FEATURES = ["fund_per", "fund_pbr", "fund_div", "fund_earnings_yield"]

FEATURE_COLS = CHART_FEATURES + FUND_FEATURES


def make_fundamentals_extra_fn(start, end):
    """extra_feature_fn(code, ohlcv): 해당 code의 재무를 ohlcv 날짜에 as-of 정렬해 반환."""
    def _fn(code, ohlcv):
        try:
            f = stock.get_market_fundamental(start, end, code)
        except Exception as e:
            log(f"    · {code}: 재무 조회 실패({type(e).__name__}) → 재무 NaN")
            f = None
        if f is None or f.empty:
            return pd.DataFrame({c: [float("nan")] * len(ohlcv) for c in FUND_FEATURES})

        # 인덱스(날짜) → date 컬럼(YYYYMMDD str)으로 변환
        f = f.copy()
        f.index.name = "date"
        f = f.reset_index()
        f["date"] = pd.to_datetime(f["date"]).dt.strftime("%Y%m%d")

        # PER=0 등 이상치는 NaN(파생 이익수익률의 0나눗셈 방지)
        for col in ["PER", "PBR", "DIV"]:
            if col in f.columns:
                f[col] = pd.to_numeric(f[col], errors="coerce")
        f.loc[f.get("PER", 0) <= 0, "PER"] = float("nan")

        fund = pd.DataFrame({
            "date": f["date"],
            "fund_per": f.get("PER"),
            "fund_pbr": f.get("PBR"),
            "fund_div": f.get("DIV"),
        })
        fund["fund_earnings_yield"] = 1.0 / fund["fund_per"]

        joined = join_fundamentals_asof(ohlcv, fund)
        return joined
    return _fn


def build_rebalances():
    """D와 동일: 연 1회(각 해 첫 거래일) point-in-time 거래대금 상위 TOP_N 유니버스."""
    firsts = annual_rebalance_dates(START, END)
    selector = UniverseSelector()
    rebs = {}
    for as_of in firsts:
        codes = selector.get_universe(as_of, top_n=TOP_N)
        if codes:
            rebs[as_of] = codes
    return rebs


def main():
    log(f"[1] 시점별 유니버스 재선정 (연 1회, 거래대금 상위 {TOP_N}) — D와 동일")
    rebalances = build_rebalances()
    if not rebalances:
        log("유니버스 선정 실패(KRX 다운). 중단."); return
    for as_of, codes in rebalances.items():
        log(f"    {as_of}: {len(codes)}종목")
    union = sorted({c for codes in rebalances.values() for c in codes})
    log(f"    유니버스 합집합 {len(union)}종목")

    log(f"[2] 패널 구축: OHLCV+재무(as-of) {START}~{END} (합집합 {len(union)}종목)")
    extra_fn = make_fundamentals_extra_fn(START, END)
    panel = build_panel(union, START, END, HORIZON, COST, FEATURE_COLS,
                        extra_feature_fn=extra_fn)
    if panel.empty:
        log("패널 비어있음. 중단."); return
    log(f"    조정 전 {len(panel)}행 → 시점별 유니버스 멤버십 필터")
    panel = filter_panel_to_universe(panel, rebalances)
    if panel.empty:
        log("필터 후 패널 비어있음. 중단."); return
    log(f"    필터 후 패널 행수={len(panel)}, 라벨 매수비율={panel['label'].mean():.3f}")

    log(f"[3~6] walk-forward 평가 (embargo={EMBARGO}, lockbox={LOCKBOX}, 차트16+재무4)")
    out = evaluate_folds(panel, FOLDS, FEATURE_COLS, EMBARGO, HORIZON, COST,
                         lockbox=LOCKBOX, top_k_frac=0.2)
    fm = out["fold_metrics"]
    if not fm:
        log("유효 폴드 없음."); return

    for m in fm:
        log(f"    검증 {m['val']}: 전략순수익={m['strategy_net']:+.4f} "
            f"바보={m['dumb_net']:+.4f} 지수={m['index_ret']:+.4f} "
            f"(상위 {m['top_k']}/{m['n_total']} 매매)")

    log("[신뢰성 리포트]")
    rep = reliability_report(fm, n_trials=1, cost=COST)
    ev = rep["eval"]
    log(f"    성공={ev['success']} ({ev['n_beat']}/{ev['n_folds']} 승리, "
        f"통과기준 {ev['required_to_pass']}, 마진={ev['margin']:.4f})")
    log(f"    전략순수익 평균={rep['strategy_net_mean']:+.4f} 표준편차={rep['strategy_net_std']:.4f}")
    log(f"    기준선 초과 폴드(n_positive_excess)={rep['n_positive_excess']}/{rep['n_folds']} "
        f"(0이면 한 번도 기준선을 못 이김)")
    log(f"    폴드간 Sharpe={rep['sharpe_across_folds']} "
        f"(폴드 수 적어 추정 약함)")

    log("[C1 판정]")
    if rep["n_positive_excess"] > 0:
        log(f"    C1(재무) 기준선 초과 = 있음 "
            f"({rep['n_positive_excess']}/{rep['n_folds']} 폴드에서 최선 기준선 초과)")
    else:
        log("    C1(재무) 기준선 초과 = 없음 "
            "(어느 폴드도 max(바보,지수)를 순수익으로 이기지 못함) → 대형주 엣지 없음")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"[오류] {type(e).__name__}: {e}")
        sys.exit(1)
