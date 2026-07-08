"""ML 신호 파이프라인 실데이터 엔드투엔드 데모 (T01~T06 조립).

수집→피처(T03)→라벨/실현손익(T02)→walk-forward 분할(T04)→LightGBM 학습(T05)
→상위 신호 백테스트+성공 판정(T06). 소규모 유니버스로 빠르게 1회 실행한다.

주의: point-in-time 분할조정(D1)·시점별 유니버스 재선정(D2)·데모 서브셋. 상폐 종목
미포함으로 생존 편향은 잔존(B2에서 완화) → 성능 낙관. 데모용.
"""
import sys
from dotenv import load_dotenv
load_dotenv()  # pykrx import 전에 KRX 자격증명 로드 (시장전체·지수 엔드포인트 로그인)

import numpy as np
import pandas as pd
from pykrx import stock

from src.ml.universe import UniverseSelector
from src.ml.features import CausalFeatureBuilder
from src.ml.labels import make_labels, make_returns
from src.ml.splits import make_folds
from src.ml.model import SignalModel
from src.ml.backtest import backtest_fold
from src.ml.reliability import reliability_report
from src.ml.prices import adjust_ohlcv, derive_splits
from src.ml.universe_schedule import filter_panel_to_universe

# D2: 시점별 유니버스 재선정(연 1회) + 5폴드 walk-forward + 락박스 봉인.
# TOP_N은 데모 서브셋(런타임 절약). 코드는 100~200을 지원한다(D2 이슈 기준).
TOP_N = 30
START, END = "20190101", "20241231"
FOLDS = [("20200101", "20201231"), ("20210101", "20211231"),
         ("20220101", "20221231"), ("20230101", "20231231"),
         ("20240101", "20241231")]
LOCKBOX = ("20240101", "20241231")  # 최종 봉인 — D2에서는 개봉하지 않음(D3에서 1회)
# KRX 시장전체 by_ticker 엔드포인트 다운 시 폴백: 코스피 대형주(상폐 리스크 낮음)
FALLBACK_CODES = ["005930", "000660", "373220", "207940", "005380", "000270",
                  "068270", "005490", "035420", "035720", "105560", "055550"]
EMBARGO = 5
HORIZON = 5
COST = 0.007
FEATURE_COLS = ["ma_5", "ma_20", "ma_50", "ma_60", "rsi_14", "macd_line",
                "macd_signal", "macd_histogram", "bb_upper", "bb_middle",
                "bb_lower", "bb_pct_b", "stoch_k", "stoch_d", "obv", "obv_trend"]


def log(msg):
    print(msg, flush=True)


_PYKRX_COLMAP = {"시가": "open", "고가": "high", "저가": "low",
                 "종가": "close", "거래량": "volume", "등락률": "change"}


def _fmt_pykrx(df):
    """pykrx OHLCV(한글 컬럼)를 파이프라인 표준 컬럼으로 정규화한다(거래대금 등은 버림)."""
    df = df.rename(columns=_PYKRX_COLMAP)[list(_PYKRX_COLMAP.values())].copy()
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = df["date"].astype(str)
    return df


def fetch_pit_ohlcv(code):
    """원본가·back-adjusted를 비교해 분할을 복원하고 point-in-time 포워드 조정한 OHLCV(D1).

    pykrx 기본 수정주가는 '오늘' 기준 소급 조정이라 미래참조 누수. 원본가에서
    분할 이벤트만 추출해 포워드 적용하면 과거 봉 불변·점프 제거를 동시에 만족한다.
    """
    raw = stock.get_market_ohlcv(START, END, code, adjusted=False)
    adj = stock.get_market_ohlcv(START, END, code, adjusted=True)
    if raw is None or raw.empty:
        return pd.DataFrame()
    raw, adj = _fmt_pykrx(raw), _fmt_pykrx(adj)
    return adjust_ohlcv(raw, derive_splits(raw, adj))


def build_panel(codes):
    """유니버스 각 종목의 (date, 피처16, label, gross_ret) 행을 모아 하나의 패널로."""
    builder = CausalFeatureBuilder()
    rows = []
    for code in codes:
        ohlcv = fetch_pit_ohlcv(code)
        if ohlcv is None or ohlcv.empty or len(ohlcv) < 80:
            log(f"  - {code}: 데이터 부족, 건너뜀")
            continue
        feats = builder.build_all(ohlcv)
        # pykrx date("2021-01-04")를 make_folds 출력과 같은 YYYYMMDD로 통일
        feats["date"] = pd.to_datetime(ohlcv["date"]).dt.strftime("%Y%m%d").values
        feats["label"] = make_labels(ohlcv, horizon=HORIZON, cost=COST).values
        feats["gross_ret"] = make_returns(ohlcv, horizon=HORIZON).values
        feats["code"] = code
        rows.append(feats.dropna(subset=FEATURE_COLS + ["label", "gross_ret"]))
        log(f"  - {code}: {len(rows[-1])}행")
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def _trading_days(start, end):
    """코스피 지수 거래일(YYYYMMDD) 리스트 — 유니버스 리밸런스 as_of의 유효 기준."""
    idx = stock.get_index_ohlcv(start, end, "1001")
    return [d.strftime("%Y%m%d") for d in idx.index]


def build_rebalances():
    """연 1회(각 해 첫 거래일) point-in-time 유니버스 재선정. {as_of: codes}.

    각 as_of 그 날짜 데이터만으로 거래대금 상위를 뽑으므로 미래참조가 없다.
    """
    days = _trading_days(START, END)
    firsts, seen = [], set()
    for d in days:
        if d[:4] not in seen:
            seen.add(d[:4]); firsts.append(d)
    selector = UniverseSelector()
    rebs = {}
    for as_of in firsts:
        codes = selector.get_universe(as_of, top_n=TOP_N)
        if codes:
            rebs[as_of] = codes
    return rebs


def index_forward_return(start, end):
    """코스피 지수의 HORIZON일 선도수익 평균. 지수 피드 다운 시 None 반환(프록시로 대체)."""
    try:
        idx = stock.get_index_ohlcv(start, end, "1001")
        close = idx["종가"].to_numpy(dtype=float)
        fwd = [close[t + HORIZON] / close[t] - 1.0 for t in range(len(close) - HORIZON)]
        return float(np.mean(fwd)) if fwd else None
    except Exception:
        return None


def main():
    log(f"[1] 시점별 유니버스 재선정 (연 1회, 거래대금 상위 {TOP_N})")
    rebalances = build_rebalances()
    if not rebalances:
        log("    ⚠ KRX by_ticker 다운 → 대형주 고정 목록으로 폴백(단일 리밸런스)")
        rebalances = {START: FALLBACK_CODES}
    for as_of, codes in rebalances.items():
        log(f"    {as_of}: {len(codes)}종목")
    union = sorted({c for codes in rebalances.values() for c in codes})
    log(f"    유니버스 합집합 {len(union)}종목")

    log(f"[2] 패널 구축: OHLCV {START}~{END} (합집합 {len(union)}종목)")
    panel = build_panel(union)
    if panel.empty:
        log("패널 비어있음. 중단."); return
    log(f"    조정 전 {len(panel)}행 → 시점별 유니버스 멤버십 필터 적용")
    panel = filter_panel_to_universe(panel, rebalances)
    if panel.empty:
        log("필터 후 패널 비어있음. 중단."); return
    log(f"    필터 후 {len(panel)}행, 라벨 매수비율={panel['label'].mean():.3f}")

    log(f"[3] walk-forward 분할 (embargo={EMBARGO}, lockbox={LOCKBOX})")
    dates = sorted(panel["date"].unique())
    folds = make_folds(dates, FOLDS, embargo=EMBARGO, lockbox=LOCKBOX)
    for f in folds:
        tag = "  [LOCKBOX·봉인]" if f["is_lockbox"] else ""
        log(f"    학습 {f['train']} → 검증 {f['val']}{tag}")

    log("[4~6] 폴드별 학습→예측→백테스트 (락박스 폴드는 D2에서 개봉 안 함)")
    fold_metrics = []
    sample_reason = None
    for f in folds:
        if f["is_lockbox"]:
            log(f"    검증 {f['val']}: 락박스 봉인 — D2 미개봉(D3 최종 1회)"); continue
        (tr_s, tr_e), (va_s, va_e) = f["train"], f["val"]
        tr = panel[(panel["date"] >= tr_s) & (panel["date"] <= tr_e)]
        va = panel[(panel["date"] >= va_s) & (panel["date"] <= va_e)]
        if len(tr) < 50 or len(va) < 20:
            log(f"    검증 {f['val']}: 표본 부족(train={len(tr)}, val={len(va)}), 건너뜀"); continue

        model = SignalModel(threshold=0.5).fit(tr[FEATURE_COLS], tr["label"].astype(int))
        va = va.copy()
        va["prob"] = model.predict_proba(va[FEATURE_COLS])

        top_k = max(1, int(len(va) * 0.2))  # 확률 상위 20%만 매매
        bt = backtest_fold(va[["prob", "gross_ret"]], top_k=top_k, cost=COST)
        idx_ret = index_forward_return(va_s, va_e)
        idx_src = "지수"
        if idx_ret is None:  # 지수 피드 다운 → 유니버스 등가중 선도수익 프록시
            idx_ret = float(va["gross_ret"].mean())
            idx_src = "지수프록시(등가중)"
        fold_metrics.append({"strategy_net": bt["strategy_net"],
                             "dumb_net": bt["dumb_net"], "index_ret": idx_ret})
        log(f"    검증 {f['val']}: 전략순수익={bt['strategy_net']:+.4f} "
            f"바보={bt['dumb_net']:+.4f} {idx_src}={idx_ret:+.4f} "
            f"(상위 {top_k}/{bt['n_total']} 매매)")

        if sample_reason is None:
            top_row = va.sort_values("prob", ascending=False).iloc[[0]]
            sample_reason = (top_row["code"].iloc[0], top_row["date"].iloc[0],
                             model.predict_one(top_row[FEATURE_COLS]))

    if not fold_metrics:
        log("유효 폴드 없음."); return

    log("[성공 판정 + 신뢰성 리포트 (D3)]")
    rep = reliability_report(fold_metrics, n_trials=1, cost=COST)
    ev = rep["eval"]
    log(f"    성공={ev['success']}  ({ev['n_beat']}/{ev['n_folds']} 승리, "
        f"통과기준 {ev['required_to_pass']}, 마진={ev['margin']:.4f})")
    log(f"    전략순수익 평균={rep['strategy_net_mean']:+.4f} 표준편차={rep['strategy_net_std']:.4f} "
        f"편차범위={rep['strategy_net_spread']:.4f}")
    log(f"    기준선 초과 폴드={rep['n_positive_excess']}/{rep['n_folds']} "
        f"(0이면 한 번도 기준선을 못 이김)")
    sr = rep["sharpe_across_folds"]
    log(f"    폴드간 Sharpe={sr:+.3f} deflated임계치={rep['deflated_sharpe_threshold']:.3f} "
        f"통과={rep['passes_deflated_sharpe']}  (폴드 수 적어 추정 약함)")
    res = rep  # 경고 출력 재사용

    if sample_reason:
        code, d, pred = sample_reason
        log(f"[예측 예시] {code} @ {d}: {pred['signal']} (prob={pred['prob']:.3f})")
        for r in pred["reasons"]:
            log(f"    · {r['feature']}={r['value']:.2f} SHAP={r['shap']:+.4f} [{r['direction']}]")
        log(f"    ⚠ {pred['disclaimer']}")

    log("[경고]")
    for w in res["warnings"]:
        log(f"    ⚠ {w}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"[오류] {type(e).__name__}: {e}")
        sys.exit(1)
