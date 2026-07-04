DEFAULT_EXPECTED_RETURN = 0.15
DEFAULT_MAX_LOSS = 0.10


class PriceTargetCalculator:
    def suggest(self, current_price: float,
                expected_return: float = DEFAULT_EXPECTED_RETURN,
                max_loss: float = DEFAULT_MAX_LOSS) -> dict:
        """현재가 기반 목표가·손절가와 리스크/리워드 비율을 계산한다."""
        target_price = round(current_price * (1 + expected_return))
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
        }
