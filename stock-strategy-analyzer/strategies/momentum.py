from __future__ import annotations

from scoring.momentum_scoring import clip_score, final_decision, momentum_grade, risk_level


def _momentum_score(base: dict, volume_ratio: float, volume_ma5_ratio: float, breakout: str) -> float:
    score = 0.0

    if breakout == "突破":
        score += 25
    elif 0 <= base["distance_to_recent_high_pct"] <= 3:
        score += 10

    if volume_ratio >= 2:
        score += 20
    elif volume_ratio >= 1.5:
        score += 12
    elif volume_ratio >= 1:
        score += 5

    if volume_ma5_ratio >= 1.5:
        score += 10
    elif volume_ma5_ratio >= 1.2:
        score += 5

    if base["close"] > base["ma5"] > base["ma10"] > base["ma20"] > base["ma60"]:
        score += 20
    elif base["close"] > base["ma20"] > base["ma60"]:
        score += 10

    if 8 <= base["return_5d_pct"] <= 20:
        score += 10
    elif 3 <= base["return_5d_pct"] < 8:
        score += 5

    if 15 <= base["return_20d_pct"] <= 40:
        score += 10
    elif 8 <= base["return_20d_pct"] < 15:
        score += 5

    if base["close"] > base["ma20"] and base["close"] > base["ma60"]:
        score += 5

    if base["return_5d_pct"] > 30:
        score -= 15
    if base["return_20d_pct"] > 60:
        score -= 15
    if base["atr_pct"] > 8:
        score -= 10
    if base["atr_pct"] > 12:
        score -= 10

    if base["close"] < base["ma20"]:
        score = min(score, 49)
    if volume_ratio < 0.8:
        score = min(score, 59)

    return clip_score(score)


def _risk_score(base: dict, volume_ratio: float, upper_shadow_pct: float, breakout: str) -> float:
    score = 0.0
    atr_pct = base["atr_pct"]
    if atr_pct < 2:
        score += 5
    elif atr_pct < 4:
        score += 15
    elif atr_pct < 6:
        score += 30
    elif atr_pct < 8:
        score += 45
    else:
        score += 60

    d_ma20 = base["distance_to_ma20_pct"]
    if d_ma20 > 20:
        score += 30
    elif d_ma20 > 12:
        score += 20
    elif d_ma20 > 6:
        score += 10

    r5 = base["return_5d_pct"]
    if r5 > 30:
        score += 30
    elif r5 > 20:
        score += 20
    elif r5 > 12:
        score += 10

    r20 = base["return_20d_pct"]
    if r20 > 60:
        score += 25
    elif r20 > 40:
        score += 15

    if breakout == "突破" and volume_ratio < 1.5:
        score += 25
    elif 0 <= base["distance_to_recent_high_pct"] <= 3 and volume_ratio < 1:
        score += 15

    if upper_shadow_pct >= 5:
        score += 20
    elif upper_shadow_pct >= 3:
        score += 10

    if base["volume_ma20"] < 100000:
        score += 40
    elif base["volume_ma20"] < 500000:
        score += 20

    return clip_score(score)


def _pass_filter(mode: str, payload: dict) -> bool:
    if mode == "loose":
        return payload["momentum_score"] >= 55 and payload["risk_score"] < 80 and payload["close"] > payload["ma20"]
    if mode == "standard":
        return (
            payload["momentum_score"] >= 65
            and payload["risk_score"] < 70
            and payload["close"] > payload["ma20"]
            and payload["volume_ratio"] >= 1.2
        )
    return (
        payload["momentum_score"] >= 80
        and payload["risk_score"] < 60
        and payload["close"] > payload["ma20"]
        and payload["close"] > payload["ma60"]
        and payload["volume_ratio"] >= 1.5
        and payload["risk_level"] in {"low", "medium"}
    )


def analyze_momentum(base: dict, mode: str, bar: dict) -> dict:
    volume_ratio = 0 if base["volume_ma20"] <= 0 else base["volume"] / base["volume_ma20"]
    volume_ma5_ratio = 0 if base["volume_ma20"] <= 0 else base["volume_ma5"] / base["volume_ma20"]
    upper_shadow_pct = (bar["High"] - max(bar["Open"], bar["Close"])) / bar["Close"] * 100 if bar["Close"] > 0 else 0

    breakout = "突破" if base["close"] > base["recent_high"] else "接近" if 0 <= base["distance_to_recent_high_pct"] <= 3 else "未接近"
    m_score = _momentum_score(base, volume_ratio, volume_ma5_ratio, breakout)
    m_grade = momentum_grade(m_score)
    r_score = _risk_score(base, volume_ratio, upper_shadow_pct, breakout)
    r_level = risk_level(r_score)

    breakout_status = {
        "突破": "突破 lookback 區間高點",
        "接近": "接近 lookback 區間高點",
        "未接近": "尚未接近突破",
    }[breakout]

    if volume_ratio >= 2:
        volume_status = f"成交量為 20 日均量 {volume_ratio:.2f} 倍，量能明顯放大"
    elif volume_ratio >= 1:
        volume_status = "成交量略高於 20 日均量"
    else:
        volume_status = "成交量不足"

    if base["close"] > base["ma5"] > base["ma10"] > base["ma20"] > base["ma60"]:
        trend_status = "均線多頭排列"
    elif base["close"] > base["ma20"] > base["ma60"]:
        trend_status = "股價位於 MA20 與 MA60 之上"
    elif base["close"] < base["ma20"]:
        trend_status = "股價跌破 MA20，短線轉弱"
    else:
        trend_status = "趨勢結構中性"

    if base["return_5d_pct"] > 30:
        overheat_status = "短線漲幅過熱，不建議追高"
    elif base["return_5d_pct"] > 12:
        overheat_status = "近 5 日漲幅偏大，追高風險升高"
    else:
        overheat_status = "短線漲幅正常"

    payload = {
        **base,
        "momentum_score": m_score,
        "momentum_grade": m_grade,
        "risk_score": r_score,
        "risk_level": r_level,
        "final_decision": final_decision(m_grade, r_level),
        "volume_ratio": volume_ratio,
        "volume_ma5_ratio": volume_ma5_ratio,
        "upper_shadow_pct": upper_shadow_pct,
        "breakout_status": breakout_status,
        "volume_status": volume_status,
        "trend_status": trend_status,
        "overheat_status": overheat_status,
    }

    reasons = [
        f"收盤價{breakout_status}，價格進入動能觀察區",
        volume_status,
        trend_status,
        f"近 5 日漲幅為 {base['return_5d_pct']:.2f}%，{overheat_status}",
        f"ATR 波動率為 {base['atr_pct']:.2f}%，需搭配風險控管",
        f"動能分數為 {m_score:.2f}，風險分數為 {r_score:.2f}",
    ]

    if r_level == "high":
        reasons.append("風險等級偏高，若要操作應降低部位並嚴格執行停損")
    if r_level == "extreme":
        reasons.append("風險等級極高，即使動能強，也不建議追高")
    if base["close"] < base["ma20"]:
        reasons.append("股價跌破 MA20，短線動能結構轉弱")
    if volume_ratio < 1:
        reasons.append("成交量低於 20 日均量，動能確認不足")
    if upper_shadow_pct >= 3:
        reasons.append("當日上影線偏長，代表上方賣壓增加")

    passed = _pass_filter(mode, payload)
    reasons.append(f"{'符合' if passed else '不符合'} {mode} 篩選條件")

    payload["passed_filter"] = passed
    payload["reasons"] = reasons
    return payload
