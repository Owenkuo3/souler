from __future__ import annotations


def get_volatility_level(atr_pct: float) -> str:
    if atr_pct < 2:
        return "low"
    if atr_pct < 4:
        return "medium"
    if atr_pct < 6:
        return "high"
    return "extreme"


def calculate_risk_grade(
    trend: str,
    expected_return_pct: float,
    expected_loss_pct: float,
    risk_reward_ratio: float | None,
    atr_pct: float,
    volatility_level: str,
) -> str:
    if trend == "weak" or expected_loss_pct > 10 or atr_pct >= 8 or expected_return_pct <= 0:
        return "E"

    ratio = risk_reward_ratio if risk_reward_ratio is not None else -1

    if ratio >= 3 and trend == "bullish" and expected_loss_pct <= 5:
        grade = "A"
    elif ratio >= 2 and trend in {"bullish", "neutral_bullish"} and expected_loss_pct <= 8:
        grade = "B"
    elif ratio >= 1.2:
        grade = "C"
    else:
        grade = "D"

    if volatility_level == "extreme" and grade in {"A", "B"}:
        grade = "C"
    return grade
