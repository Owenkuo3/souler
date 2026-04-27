import json
from datetime import datetime
from typing import Any


ALLOWED_LOOKBACK = {20, 60, 120, 240}
ALLOWED_MODE = {"loose", "standard", "strict"}
ALLOWED_STRATEGY = {"risk_reward", "momentum"}


class AnalyzerError(Exception):
    """Domain error rendered as JSON."""


def parse_analysis_date(analysis_date: str | None):
    if analysis_date is None:
        return None
    try:
        return datetime.strptime(analysis_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise AnalyzerError("analysis_date 格式錯誤，請使用 YYYY-MM-DD") from exc


def round_value(value: Any):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return value


def round_payload(payload: dict) -> dict:
    rounded = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            rounded[key] = round_payload(value)
        elif isinstance(value, list):
            rounded[key] = [round_value(item) for item in value]
        else:
            rounded[key] = round_value(value)
    return rounded


def error_json(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


def json_output(payload: dict) -> str:
    return json.dumps(round_payload(payload), ensure_ascii=False, indent=2)
