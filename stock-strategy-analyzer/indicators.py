from __future__ import annotations

import numpy as np
import pandas as pd

from utils import AnalyzerError


def compute_indicators(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    out = df.copy()

    out["MA5"] = out["Close"].rolling(5).mean()
    out["MA10"] = out["Close"].rolling(10).mean()
    out["MA20"] = out["Close"].rolling(20).mean()
    out["MA60"] = out["Close"].rolling(60).mean()
    out["MA120"] = out["Close"].rolling(120).mean()

    prev_close = out["Close"].shift(1)
    tr = pd.concat(
        [
            out["High"] - out["Low"],
            (out["High"] - prev_close).abs(),
            (out["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["ATR14"] = tr.rolling(14).mean()

    out["Volume_MA5"] = out["Volume"].rolling(5).mean()
    out["Volume_MA20"] = out["Volume"].rolling(20).mean()

    out["recent_high"] = out["High"].rolling(lookback).max()
    out["recent_low"] = out["Low"].rolling(lookback).min()

    out["return_5d_pct"] = (out["Close"] / out["Close"].shift(5) - 1.0) * 100
    out["return_20d_pct"] = (out["Close"] / out["Close"].shift(20) - 1.0) * 100
    out["return_60d_pct"] = (out["Close"] / out["Close"].shift(60) - 1.0) * 100

    out["distance_to_ma20_pct"] = (out["Close"] - out["MA20"]) / out["Close"] * 100
    out["distance_to_recent_high_pct"] = (out["recent_high"] - out["Close"]) / out["Close"] * 100
    out["distance_to_recent_low_pct"] = (out["Close"] - out["recent_low"]) / out["Close"] * 100
    out["atr_pct"] = np.where(out["Close"] > 0, out["ATR14"] / out["Close"] * 100, np.nan)

    required = [
        "MA5",
        "MA10",
        "MA20",
        "MA60",
        "MA120",
        "ATR14",
        "Volume_MA5",
        "Volume_MA20",
        "recent_high",
        "recent_low",
        "return_5d_pct",
        "return_20d_pct",
        "return_60d_pct",
        "distance_to_ma20_pct",
        "distance_to_recent_high_pct",
        "distance_to_recent_low_pct",
        "atr_pct",
    ]
    if out[required].iloc[-1].isna().any():
        raise AnalyzerError("資料不足，無法計算 MA120 / ATR14 / lookback，或指標出現 NaN")

    return out
