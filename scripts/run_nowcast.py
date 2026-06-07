#!/usr/bin/env python3
"""Run the latest expanding-window backtest and report summary metrics."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from regional_activity_nowcast.evaluate import expanding_window_backtest, rmse_table, write_report_artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monthly", default="data/processed/monthly_indicators.csv")
    parser.add_argument("--target", default="data/processed/quarterly_gdp.csv")
    parser.add_argument("--min-train-quarters", type=int, default=12)
    args = parser.parse_args()

    monthly = pd.read_csv(args.monthly, parse_dates=["date"])
    target = pd.read_csv(args.target, parse_dates=["date"])
    results = expanding_window_backtest(monthly, target, min_train_quarters=args.min_train_quarters)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    results.to_csv("data/processed/backtest_results.csv", index=False)
    write_report_artifacts(monthly, target, results)
    print(rmse_table(results).to_string(index=False))


if __name__ == "__main__":
    main()

