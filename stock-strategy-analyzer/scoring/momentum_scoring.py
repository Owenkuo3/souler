from __future__ import annotations


def clip_score(value: float, lower: float = 0, upper: float = 100) -> float:
    return max(lower, min(upper, value))


def momentum_grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "E"


def risk_level(score: float) -> str:
    if score < 30:
        return "low"
    if score < 60:
        return "medium"
    if score < 80:
        return "high"
    return "extreme"


def final_decision(grade: str, level: str) -> str:
    if grade == "A" and level in {"low", "medium"}:
        return "強勢動能，風險尚可控，可列入觀察"
    if grade == "A" and level == "high":
        return "動能很強，但追高與波動風險偏高，只適合小部位或等待拉回"
    if grade == "A" and level == "extreme":
        return "動能很強，但風險過高，不建議追高"
    if grade == "B" and level in {"low", "medium"}:
        return "偏強觀察，尚未完全加速"
    if grade == "B" and level in {"high", "extreme"}:
        return "有動能，但風險偏高，等待更好的進場位置"
    if grade == "C":
        return "有部分動能，但訊號不明確"
    return "動能不足，不符合飆股條件"
