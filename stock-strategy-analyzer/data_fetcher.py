from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from utils import AnalyzerError


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_ohlcv(symbol: str, lookback: int, analysis_date: date | None) -> tuple[pd.DataFrame, pd.Timestamp]:
    end_date = analysis_date or date.today()
    start_date = end_date - timedelta(days=(lookback + 200) * 3)

    try:
        df = yf.download(
            symbol,
            start=start_date.strftime("%Y-%m-%d"),
            end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as exc:  # pragma: no cover
        raise AnalyzerError("抓取資料失敗，請稍後再試") from exc

    if df is None or df.empty:
        raise AnalyzerError("symbol 抓不到資料或代號無效")

    df = _normalize_columns(df).copy()
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise AnalyzerError(f"資料欄位缺失：{', '.join(missing)}")

    df = df[REQUIRED_COLUMNS].dropna().sort_index()
    if df.empty:
        raise AnalyzerError("抓到的資料為空，無法分析")

    if analysis_date is not None and pd.Timestamp(analysis_date) < df.index[0]:
        raise AnalyzerError("analysis_date 早於資料起始日")

    eligible = df.index[df.index <= pd.Timestamp(end_date)]
    if len(eligible) == 0:
        raise AnalyzerError("analysis_date 之前無有效交易日資料")

    effective_date = eligible[-1]
    df = df[df.index <= effective_date].copy()

    min_required = max(120, lookback, 60) + 20
    if len(df) < min_required:
        raise AnalyzerError("資料不足，無法計算 MA120 或 lookback 區間")

    return df, effective_date
