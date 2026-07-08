"""Phase C 실험 C2: 중소형주(저순위 밴드) 유니버스로 차트-only 엣지 검증.

가설: 대형주(D 베이스라인)는 너무 효율적이라 못 이긴 것일 수 있다. 유니버스를
거래대금 순위 중하위 밴드(중소형주)로 바꾸면 차트만으로 엣지가 생기나?

D 베이스라인과의 유일한 차이는 유니버스뿐 — 피처(차트 16개)·기간·폴드·비용·엠바고
모두 동일해야 공정한 A/B. point-in-time 원칙(각 as_of 그 시점 데이터로만 밴드 선정)을
그대로 지킨다(미래참조 금지).
"""
import sys
from dotenv import load_dotenv
load_dotenv()  # pykrx import 전 KRX 자격증명 로드

import numpy as np

from src.ml.pipeline import (
    build_panel, annual_rebalance_dates, evaluate_folds, log,
)
from src.ml.universe import UniverseSelector
from src.ml.universe_schedule import filter_panel_to_universe
from src.ml.reliability import reliability_report

# --- D와 동일 설정 (유니버스만 교체) ---
START, END = "20190101", "20241231"
HORIZON = 5
COST = 0.007
EMBARGO = 5
FOLDS = [("20200101", "20201231"), ("20210101", "20211231"),
         ("20220101", "20221231"), ("20230101", "20231231"),
         ("20240101", "20241231")]
LOCKBOX = ("20240101", "20241231")
FEATURE_COLS = ["ma_5", "ma_20", "ma_50", "ma_60", "rsi_14", "macd_line",
                "macd_signal", "macd_histogram", "bb_upper", "bb_middle",
                "bb_lower", "bb_pct_b", "stoch_k", "stoch_d", "obv", "obv_trend"]

# --- C2 유니버스: 중소형 밴드 ---
# 시장 선택 근거: KOSPI 거래대금 순위 100~140위(0-기반 [100,140)) 밴드.
#   - 대형주(D)는 상위 ~30위권이었다. 100위 밑은 중형주 영역이라 "대형주 효율성"
#     가설을 검증하기에 적합하고, 상폐/데이터부족 리스크가 소형주보다 낮다.
#   - 밴드 폭 40: 종목수를 D 수준(~수십)으로 맞춰 런타임을 통제(no silent caps —
#     이 상한은 여기 명시).
# min_value(거래대금 하한): 5e8 KRW(=5억원/일). 100위권 KOSPI 종목의 일 거래대금은
#   보통 수십억이므로 5억은 극저유동성·상장폐지 직전 종목만 걸러내는 안전 하한이다.
#   (D와의 유일 차이는 밴드 위치이며, 하한은 슬리피지 방지용 위생 필터일 뿐.)
MARKET = "KOSPI"
BAND_START, BAND_END = 100, 140
MIN_VALUE = 5e8


def build_rebalances():
    """연 1회 point-in-time 중소형 밴드 재선정. {as_of: codes}."""
    as_ofs = annual_rebalance_dates(START, END)
    selector = UniverseSelector()
    rebs = {}
    for as_of in as_ofs:
        codes = selector.get_universe_band(
            as_of, start_rank=BAND_START, end_rank=BAND_END,
            market=MARKET, min_value=MIN_VALUE)
        log(f"    {as_of}: {len(codes)}종목 (밴드 [{BAND_START},{BAND_END}) {MARKET})")
        if codes:
            rebs[as_of] = codes
    return rebs


def main():
    log(f"[C2] 중소형 밴드 유니버스: {MARKET} 거래대금 [{BAND_START},{BAND_END}) "
        f"min_value={MIN_VALUE:.0f}원")
    log("[1] 시점별 유니버스 재선정 (연 1회, point-in-time)")
    rebalances = build_rebalances()
    if not rebalances:
        log("    ⚠ 유니버스 선정 실패(KRX by_ticker 다운/로그인 실패). 중단.")
        return
    union = sorted({c for codes in rebalances.values() for c in codes})
    log(f"    유니버스 합집합 {len(union)}종목")

    log(f"[2] 패널 구축: OHLCV {START}~{END} (합집합 {len(union)}종목)")
    panel = build_panel(union, START, END, HORIZON, COST, FEATURE_COLS)
    if panel.empty:
        log("패널 비어있음. 중단."); return
    log(f"    조정 전 {len(panel)}행 → 시점별 유니버스 멤버십 필터")
    panel = filter_panel_to_universe(panel, rebalances)
    if panel.empty:
        log("필터 후 패널 비어있음. 중단."); return
    log(f"    필터 후 {len(panel)}행, 라벨 매수비율={panel['label'].mean():.3f}")

    log(f"[3~6] walk-forward 평가 (embargo={EMBARGO}, lockbox={LOCKBOX}, "
        f"락박스 폴드 미개봉)")
    result = evaluate_folds(panel, FOLDS, FEATURE_COLS, embargo=EMBARGO,
                            horizon=HORIZON, cost=COST, lockbox=LOCKBOX)
    fold_metrics = result["fold_metrics"]
    if not fold_metrics:
        log("유효 폴드 없음(표본 부족). 중단."); return

    log("[폴드별 성과]")
    for fm in fold_metrics:
        log(f"    검증 {fm['val']}: 전략순수익={fm['strategy_net']:+.4f} "
            f"바보={fm['dumb_net']:+.4f} 지수={fm['index_ret']:+.4f} "
            f"(상위 {fm['top_k']}/{fm['n_total']} 매매)")

    log("[신뢰성 리포트]")
    rep = reliability_report(fold_metrics, n_trials=1, cost=COST)
    ev = rep["eval"]
    log(f"    성공={ev['success']}  ({ev['n_beat']}/{ev['n_folds']} 승리, "
        f"통과기준 {ev['required_to_pass']}, 마진={ev['margin']:.4f})")
    log(f"    전략순수익 평균={rep['strategy_net_mean']:+.4f} "
        f"표준편차={rep['strategy_net_std']:.4f} 편차범위={rep['strategy_net_spread']:.4f}")
    log(f"    기준선 초과 폴드={rep['n_positive_excess']}/{rep['n_folds']} "
        f"(0이면 한 번도 기준선을 못 이김)")
    sr = rep["sharpe_across_folds"]
    sr_str = "None" if sr is None else f"{sr:+.3f}"
    log(f"    폴드간 Sharpe={sr_str} (폴드 수 적어 추정 약함)")

    log("[C2 판정]")
    beat = rep["n_positive_excess"] > 0
    log(f"    C2(중소형주) 기준선 초과 = {'있음' if beat else '없음'} "
        f"({rep['n_positive_excess']}/{rep['n_folds']} 폴드)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"[오류] {type(e).__name__}: {e}")
        sys.exit(1)
