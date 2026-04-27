from __future__ import annotations

from scoring.risk_reward_scoring import calculate_risk_grade, get_volatility_level


def _trend(close: float, ma20: float, ma60: float) -> str:
    if close > ma20 > ma60:
        return "bullish"
    if close > ma60 and ma20 <= ma60:
        return "neutral_bullish"
    if close < ma60:
        return "weak"
    return "neutral"


def _passed_filter(mode: str, payload: dict) -> bool:
    ratio = payload["risk_reward_ratio"] or 0
    close = payload["close"]
    ma20 = payload["ma20"]
    ma60 = payload["ma60"]
    volume = payload["volume"]
    volume_ma20 = payload["volume_ma20"]
    vol_level = payload["volatility_level"]
    expected_loss = payload["expected_loss_pct"]
    dist_high = payload["distance_to_recent_high_pct"]

    if mode == "loose":
        return ratio >= 1.5 and expected_loss <= 10 and close > ma60
    if mode == "standard":
        return (
            ratio >= 2
            and expected_loss <= 8
            and close > ma20
            and close > ma60
            and volume >= volume_ma20 * 0.8
            and vol_level != "extreme"
        )
    return (
        ratio >= 3
        and expected_loss <= 5
        and close > ma20
        and ma20 > ma60
        and volume >= volume_ma20
        and vol_level in {"low", "medium"}
        and dist_high >= 2
    )


def analyze_risk_reward(base: dict, mode: str) -> dict:
    close = base["close"]
    ma20 = base["ma20"]
    ma60 = base["ma60"]
    atr14 = base["atr14"]

    trend = _trend(close, ma20, ma60)
    target_price = base["recent_high"]
    structure_stop_price = base["recent_low"]
    volatility_stop_price = close - 2 * atr14
    stop_loss_price = min(structure_stop_price, volatility_stop_price)

    expected_return_pct = (target_price - close) / close * 100
    expected_loss_pct = (close - stop_loss_price) / close * 100

    if expected_return_pct <= 0:
        risk_reward_ratio = 0.0
    elif expected_loss_pct <= 0:
        risk_reward_ratio = None
    else:
        risk_reward_ratio = expected_return_pct / expected_loss_pct

    stop_atr_multiple = None if atr14 <= 0 else (close - stop_loss_price) / atr14
    volatility_level = get_volatility_level(base["atr_pct"])

    risk_grade = calculate_risk_grade(
        trend=trend,
        expected_return_pct=expected_return_pct,
        expected_loss_pct=expected_loss_pct,
        risk_reward_ratio=risk_reward_ratio,
        atr_pct=base["atr_pct"],
        volatility_level=volatility_level,
    )

    payload = {
        **base,
        "trend": trend,
        "target_price": target_price,
        "structure_stop_price": structure_stop_price,
        "volatility_stop_price": volatility_stop_price,
        "stop_loss_price": stop_loss_price,
        "expected_return_pct": expected_return_pct,
        "expected_loss_pct": expected_loss_pct,
        "risk_reward_ratio": risk_reward_ratio,
        "stop_atr_multiple": stop_atr_multiple,
        "volatility_level": volatility_level,
        "risk_grade": risk_grade,
    }

    reasons = []
    if trend in {"bullish", "neutral_bullish"}:
        reasons.append("股價位於 MA20 與 MA60 之上，趨勢偏多")
    elif trend == "weak":
        reasons.append("股價位於 MA60 下方，趨勢偏弱")
    else:
        reasons.append("趨勢尚未明確，多空力道接近")

    reasons.append(
        f"預估報酬率為 {expected_return_pct:.2f}%，預估虧損率為 {expected_loss_pct:.2f}%，風報比為 {(risk_reward_ratio or 0):.2f}"
    )
    level_zh = {"low": "低", "medium": "中等", "high": "高", "extreme": "極高"}[volatility_level]
    reasons.append(f"ATR 波動率為 {base['atr_pct']:.2f}%，屬於{level_zh}波動")

    if stop_atr_multiple is not None:
        reasons.append(f"停損距離約為 {stop_atr_multiple:.2f} 倍 ATR，停損距離合理")
        if stop_atr_multiple < 1.5:
            reasons.append("停損距離小於 1.5 倍 ATR，容易被正常波動洗出場")
        if stop_atr_multiple > 3:
            reasons.append("停損距離大於 3 倍 ATR，代表進場位置可能不佳或虧損成本偏高")

    if volatility_level == "high":
        reasons.append("ATR 波動率偏高，需降低部位或提高風險控管")
    if volatility_level == "extreme":
        reasons.append("ATR 波動率極高，即使風報比看起來不錯，也不應視為低風險")
    if expected_return_pct <= 0:
        reasons.append("目前價格已接近或高於 lookback 區間高點，上方空間有限")

    passed = _passed_filter(mode, payload)
    reasons.append(f"{'符合' if passed else '不符合'} {mode} 篩選條件")

    payload["passed_filter"] = passed
    payload["reasons"] = reasons
    return payload
