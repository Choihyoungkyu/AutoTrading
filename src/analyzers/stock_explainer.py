"""정직한 종목 상태 설명 + 리스크 표시. 예측 없음 — 현재 상태 서술과 위험 표시만."""

DISCLAIMER = "현재 상태 설명이며 투자 권유가 아닙니다."

# 임계값 단일 출처 (스펙 문서와 일치). 판단 개입 수치이므로 보수적으로.
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
DEBT_RATIO_HIGH = 200.0
PBR_UNDERVALUED = 1.0
LOW_LIQUIDITY_VALUE = 1_000_000_000  # 일 거래대금 10억원 미만 = 저유동성


def _num(v):
    """숫자로 해석 가능하면 float, 아니면 None."""
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def explain(indicators, financials, liquidity=None):
    """현재 지표·재무를 투명 규칙으로 서술/경고한다. 필드 결측 규칙은 건너뛴다."""
    technical, financial = [], []

    rsi = _num(indicators.get("rsi"))
    if rsi is not None:
        if rsi < RSI_OVERSOLD:
            technical.append({"label": "RSI", "statement": f"RSI {rsi:.0f} — 단기 과매도 구간", "severity": "info"})
        elif rsi > RSI_OVERBOUGHT:
            technical.append({"label": "RSI", "statement": f"RSI {rsi:.0f} — 단기 과매수, 과열 주의", "severity": "caution"})
        else:
            technical.append({"label": "RSI", "statement": f"RSI {rsi:.0f} — 중립 구간", "severity": "info"})

    ml, ms = _num(indicators.get("macd_line")), _num(indicators.get("macd_signal"))
    if ml is not None and ms is not None:
        up = ml > ms
        technical.append({"label": "MACD",
                          "statement": "MACD가 시그널 위 — 상승 모멘텀" if up else "MACD가 시그널 아래 — 하락 모멘텀",
                          "severity": "info"})

    m20, m50 = _num(indicators.get("ma_20")), _num(indicators.get("ma_50"))
    if m20 is not None and m50 is not None:
        up = m20 > m50
        technical.append({"label": "이동평균",
                          "statement": "단기(20)>중기(50) — 상승 배열(정배열)" if up else "단기(20)<중기(50) — 하락 배열(역배열)",
                          "severity": "info"})

    bb = indicators.get("bb_state")
    if bb == "상단":
        technical.append({"label": "볼린저밴드", "statement": "밴드 상단 — 단기 과열 주의", "severity": "caution"})
    elif bb == "하단":
        technical.append({"label": "볼린저밴드", "statement": "밴드 하단 이탈", "severity": "caution"})

    if liquidity is not None:
        tv = _num(liquidity.get("trade_value"))
        if tv is not None and tv < LOW_LIQUIDITY_VALUE:
            technical.append({"label": "유동성", "statement": "저유동성 — 슬리피지·상폐 위험 주의", "severity": "warning"})

    pbr = _num(financials.get("pbr"))
    if pbr is not None and 0 < pbr < PBR_UNDERVALUED:
        financial.append({"label": "PBR", "statement": f"PBR {pbr:.2f} — 자산 대비 저평가 구간", "severity": "info"})

    per = _num(financials.get("per"))
    if per is not None:
        if per > 0:
            financial.append({"label": "PER", "statement": f"PER {per:.1f}", "severity": "info"})
        else:
            financial.append({"label": "PER", "statement": "PER 산출 불가(적자 등)", "severity": "caution"})

    debt = _num(financials.get("debt_ratio"))
    if debt is not None and debt > DEBT_RATIO_HIGH:
        financial.append({"label": "부채비율", "statement": f"부채비율 {debt:.0f}% — 재무 부담 높음", "severity": "warning"})

    roe = _num(financials.get("roe"))
    if roe is not None and roe < 0:
        financial.append({"label": "ROE", "statement": f"ROE {roe:.1f}% — 자본 수익성 마이너스", "severity": "warning"})

    div = _num(financials.get("dividend_yield"))
    if div is not None and div > 0:
        financial.append({"label": "배당", "statement": f"배당수익률 {div:.2f}%", "severity": "info"})

    risks = [x for x in technical + financial if x["severity"] in ("caution", "warning")]
    return {"technical": technical, "financial": financial, "risks": risks, "disclaimer": DISCLAIMER}
