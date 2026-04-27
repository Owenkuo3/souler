from __future__ import annotations

import argparse

from data_fetcher import fetch_ohlcv
from indicators import compute_indicators
from strategies.momentum import analyze_momentum
from strategies.risk_reward import analyze_risk_reward
from utils import (
    ALLOWED_LOOKBACK,
    ALLOWED_MODE,
    ALLOWED_STRATEGY,
    AnalyzerError,
    error_json,
    json_output,
    parse_analysis_date,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stock Strategy Analyzer")
    parser.add_argument("--symbol", required=True, help="股票代號，例如 2330.TW 或 AAPL")
    parser.add_argument("--lookback", required=True, type=int, help="分析週期 (20/60/120/240)")
    parser.add_argument("--mode", required=True, help="篩選模式 (loose/standard/strict)")
    parser.add_argument("--strategy", required=True, help="策略模式 (risk_reward/momentum)")
    parser.add_argument("--analysis-date", dest="analysis_date", help="分析基準日 YYYY-MM-DD")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.lookback not in ALLOWED_LOOKBACK:
        raise AnalyzerError("lookback 不在允許值內，僅可使用 20/60/120/240")
    if args.mode not in ALLOWED_MODE:
        raise AnalyzerError("mode 不在允許值內，僅可使用 loose/standard/strict")
    if args.strategy not in ALLOWED_STRATEGY:
        raise AnalyzerError("strategy 不在允許值內，僅可使用 risk_reward/momentum")


def build_base_payload(args: argparse.Namespace, effective_date, row) -> dict:
    return {
        "symbol": args.symbol,
        "strategy": args.strategy,
        "analysis_date": args.analysis_date,
        "effective_analysis_date": effective_date.strftime("%Y-%m-%d"),
        "close": row["Close"],
        "volume": row["Volume"],
        "lookback_days": args.lookback,
        "filter_mode": args.mode,
        "ma5": row["MA5"],
        "ma10": row["MA10"],
        "ma20": row["MA20"],
        "ma60": row["MA60"],
        "ma120": row["MA120"],
        "volume_ma5": row["Volume_MA5"],
        "volume_ma20": row["Volume_MA20"],
        "atr14": row["ATR14"],
        "atr_pct": row["atr_pct"],
        "recent_high": row["recent_high"],
        "recent_low": row["recent_low"],
        "return_5d_pct": row["return_5d_pct"],
        "return_20d_pct": row["return_20d_pct"],
        "return_60d_pct": row["return_60d_pct"],
        "distance_to_ma20_pct": row["distance_to_ma20_pct"],
        "distance_to_recent_high_pct": row["distance_to_recent_high_pct"],
        "distance_to_recent_low_pct": row["distance_to_recent_low_pct"],
    }


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        parsed_analysis_date = parse_analysis_date(args.analysis_date)

        raw_df, effective_date = fetch_ohlcv(args.symbol, args.lookback, parsed_analysis_date)
        df = compute_indicators(raw_df, args.lookback)

        row = df.loc[effective_date]
        base = build_base_payload(args, effective_date, row)

        if args.strategy == "risk_reward":
            result = analyze_risk_reward(base, args.mode)
        else:
            result = analyze_momentum(base, args.mode, raw_df.loc[effective_date])

        print(json_output(result))
        return 0
    except AnalyzerError as exc:
        print(error_json(str(exc)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
