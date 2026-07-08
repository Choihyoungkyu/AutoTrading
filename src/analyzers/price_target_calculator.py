DEFAULT_EXPECTED_RETURN = 0.15
DEFAULT_MAX_LOSS = 0.10


class PriceTargetCalculator:
    def suggest(self, current_price: float,
                expected_return: float = DEFAULT_EXPECTED_RETURN,
                max_loss: float = DEFAULT_MAX_LOSS,
                target_price: float = None) -> dict:
        """목표가·손절가와 리스크/리워드 비율을 계산한다.
        target_price(증권사 컨센서스 평균)가 주어지면 그 값을 목표가로 쓰고
        기대수익률은 현재가 대비로 역산한다. 없으면 현재가×(1+기대수익률) 추정.
        손절가는 애널리스트가 제시하지 않으므로 현재가×(1−최대손실률) 가드레일로 둔다."""
        if target_price and target_price > 0:
            target_price = round(target_price)
            expected_return = round((target_price - current_price) / current_price, 4) if current_price else expected_return
            source = "consensus"
        else:
            target_price = round(current_price * (1 + expected_return))
            source = "estimate"
        stop_loss = round(current_price * (1 - max_loss))

        upside = target_price - current_price
        downside = current_price - stop_loss
        risk_reward_ratio = round(upside / downside, 2) if downside > 0 else None

        return {
            "current_price": current_price,
            "expected_return": expected_return,
            "max_loss": max_loss,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_reward_ratio": risk_reward_ratio,
            "source": source,
        }

    def extend(self, result: dict, high: float = None, low: float = None,
               close: float = None) -> dict:
        """기존 suggest() 결과에 upside/pivot/support/resistance/scenarios 추가.
        피벗은 직전 봉의 H/L/C로 계산(값이 없으면 support/resistance는 [])."""
        cur = result.get("current_price")
        target = result.get("target_price")
        stop = result.get("stop_loss")

        upside = round((target - cur) / cur * 100, 2) if cur else None

        pivot = None
        support, resistance = [], []
        if high is not None and low is not None and close is not None:
            pivot = round((high + low + close) / 3)
            r1 = round(2 * pivot - low)
            s1 = round(2 * pivot - high)
            r2 = round(pivot + (high - low))
            s2 = round(pivot - (high - low))
            support = [s1, s2]
            resistance = [r1, r2]

        result["upside"] = upside
        result["pivot"] = pivot
        result["support"] = support
        result["resistance"] = resistance
        opt_desc = ("증권사 컨센서스 목표가 도달 시나리오"
                    if result.get("source") == "consensus"
                    else "목표가 도달 시나리오 (기대수익 반영)")
        result["scenarios"] = {
            "optimistic": {"price": target, "desc": opt_desc},
            "neutral": {"price": cur, "desc": "현재가 유지 (횡보) 시나리오"},
            "pessimistic": {"price": stop, "desc": "손절가 도달 시나리오 (최대손실 반영)"},
        }
        return result
