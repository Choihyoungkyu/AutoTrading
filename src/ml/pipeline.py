"""ML 신호 파이프라인 공용 실험 하네스 (D 검증 이후 C 실험들이 공유).

수집→피처→라벨→walk-forward 평가를 한 곳에 모아, C1(재무)·C2(중소형주)가 동일한
방법으로 실험되도록 한다(공정 비교). 지수 수익은 index_ret_fn으로 주입 가능해
네트워크 없이도 테스트할 수 있다.

point-in-time 원칙: 분할조정(D1)·시점별 유니버스(D2)·미래참조 없는 피처(T03)를
그대로 재사용한다.
"""
from dotenv import load_dotenv
load_dotenv()  # pykrx import 전에 KRX 자격증명 로드

import numpy as np
import pandas as pd
from pykrx import stock

from src.ml.features import CausalFeatureBuilder
from src.ml.labels import make_labels, make_returns
from src.ml.splits import make_folds
from src.ml.model import SignalModel
from src.ml.backtest import backtest_fold
from src.ml.prices import adjust_ohlcv, derive_splits

_PYKRX_COLMAP = {"시가": "open", "고가": "high", "저가": "low",
                 "종가": "close", "거래량": "volume", "등락률": "change"}


def log(msg):
    print(msg, flush=True)


def _fmt_pykrx(df):
    """pykrx OHLCV(한글 컬럼)를 표준 컬럼으로 정규화한다(거래대금 등은 버림)."""
    df = df.rename(columns=_PYKRX_COLMAP)[list(_PYKRX_COLMAP.values())].copy()
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = df["date"].astype(str)
    return df


def fetch_pit_ohlcv(code, start, end):
    """원본가·back-adjusted 비교로 분할을 복원하고 point-in-time 포워드 조정한 OHLCV(D1)."""
    raw = stock.get_market_ohlcv(start, end, code, adjusted=False)
    adj = stock.get_market_ohlcv(start, end, code, adjusted=True)
    if raw is None or raw.empty:
        return pd.DataFrame()
    raw, adj = _fmt_pykrx(raw), _fmt_pykrx(adj)
    return adjust_ohlcv(raw, derive_splits(raw, adj))


def panel_rows_for(ohlcv, horizon, cost, feature_cols, code, builder=None,
                   extra_feature_fn=None):
    """한 종목 OHLCV에서 (date, 피처, label, gross_ret, code) 행을 만든다.

    extra_feature_fn(code, ohlcv) -> DataFrame(len==len(ohlcv))로 추가 피처(예: 재무)를
    붙일 수 있다. feature_cols에 그 컬럼명을 포함하면 dropna로 결측 행이 정리된다.
    """
    builder = builder or CausalFeatureBuilder()
    feats = builder.build_all(ohlcv)
    feats["date"] = pd.to_datetime(ohlcv["date"]).dt.strftime("%Y%m%d").values
    if extra_feature_fn is not None:
        extra = extra_feature_fn(code, ohlcv)
        for c in extra.columns:
            feats[c] = extra[c].values
    feats["label"] = make_labels(ohlcv, horizon=horizon, cost=cost).values
    feats["gross_ret"] = make_returns(ohlcv, horizon=horizon).values
    feats["code"] = code
    return feats.dropna(subset=feature_cols + ["label", "gross_ret"])


def build_panel(codes, start, end, horizon, cost, feature_cols,
                extra_feature_fn=None, fetch=None):
    """유니버스 각 종목의 행을 모아 하나의 패널로. fetch 주입 가능(테스트용)."""
    fetch = fetch or (lambda c: fetch_pit_ohlcv(c, start, end))
    builder = CausalFeatureBuilder()
    rows = []
    for code in codes:
        ohlcv = fetch(code)
        if ohlcv is None or ohlcv.empty or len(ohlcv) < 80:
            log(f"  - {code}: 데이터 부족, 건너뜀")
            continue
        r = panel_rows_for(ohlcv, horizon, cost, feature_cols, code,
                           builder=builder, extra_feature_fn=extra_feature_fn)
        rows.append(r)
        log(f"  - {code}: {len(r)}행")
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def annual_rebalance_dates(start, end):
    """각 해 첫 거래일(YYYYMMDD) — 코스피 지수 달력 기준."""
    idx = stock.get_index_ohlcv(start, end, "1001")
    days = [d.strftime("%Y%m%d") for d in idx.index]
    firsts, seen = [], set()
    for d in days:
        if d[:4] not in seen:
            seen.add(d[:4]); firsts.append(d)
    return firsts


def index_forward_return(start, end, horizon):
    """코스피 지수 horizon일 선도수익 평균. 피드 다운 시 None."""
    try:
        idx = stock.get_index_ohlcv(start, end, "1001")
        close = idx["종가"].to_numpy(dtype=float)
        fwd = [close[t + horizon] / close[t] - 1.0 for t in range(len(close) - horizon)]
        return float(np.mean(fwd)) if fwd else None
    except Exception:
        return None


def evaluate_folds(panel, folds, feature_cols, embargo, horizon, cost,
                   lockbox=None, top_k_frac=0.2, index_ret_fn=None):
    """walk-forward 폴드별 학습→예측→백테스트. 락박스 폴드는 평가에서 제외.

    반환: {"folds", "fold_metrics", "sample_reason"}. index_ret_fn(start,end) 주입 가능
    (기본은 코스피 지수). 지수 None이면 유니버스 등가중 선도수익 프록시로 대체한다.
    """
    if index_ret_fn is None:
        index_ret_fn = lambda s, e: index_forward_return(s, e, horizon)

    dates = sorted(panel["date"].unique())
    all_folds = make_folds(dates, folds, embargo=embargo, lockbox=lockbox)
    fold_metrics = []
    sample_reason = None
    for f in all_folds:
        if f["is_lockbox"]:
            continue
        (tr_s, tr_e), (va_s, va_e) = f["train"], f["val"]
        tr = panel[(panel["date"] >= tr_s) & (panel["date"] <= tr_e)]
        va = panel[(panel["date"] >= va_s) & (panel["date"] <= va_e)]
        if len(tr) < 50 or len(va) < 20:
            continue

        model = SignalModel(threshold=0.5).fit(tr[feature_cols], tr["label"].astype(int))
        va = va.copy()
        va["prob"] = model.predict_proba(va[feature_cols])

        top_k = max(1, int(len(va) * top_k_frac))
        bt = backtest_fold(va[["prob", "gross_ret"]], top_k=top_k, cost=cost)
        idx_ret = index_ret_fn(va_s, va_e)
        if idx_ret is None:
            idx_ret = float(va["gross_ret"].mean())  # 지수 프록시(등가중)
        fold_metrics.append({"val": f["val"], "strategy_net": bt["strategy_net"],
                             "dumb_net": bt["dumb_net"], "index_ret": idx_ret,
                             "n_total": bt["n_total"], "top_k": top_k})

        if sample_reason is None and not va.empty:
            top_row = va.sort_values("prob", ascending=False).iloc[[0]]
            sample_reason = (top_row["code"].iloc[0], top_row["date"].iloc[0],
                             model.predict_one(top_row[feature_cols]))

    return {"folds": all_folds, "fold_metrics": fold_metrics, "sample_reason": sample_reason}
