#!/usr/bin/env python3
"""Run the latest expanding-window backtest and report summary metrics."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from regional_activity_nowcast.data import load_series_registry, registry_release_lags
from regional_activity_nowcast.evaluate import expanding_window_backtest, metric_table, write_report_artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monthly", default="data/processed/monthly_indicators.csv")
    parser.add_argument("--target", default="data/processed/quarterly_gdp.csv")
    parser.add_argument("--registry", default="config/series_registry.yml")
    parser.add_argument("--min-train-quarters", type=int, default=12)
    parser.add_argument("--target-transform", choices=["level", "qoq_ann", "yoy"], default="level")
    parser.add_argument("--nowcast-lag-days", type=int, default=45)
    args = parser.parse_args()

    monthly = pd.read_csv(args.monthly, parse_dates=["date"])
    target = pd.read_csv(args.target, parse_dates=["date"])
    registry = load_series_registry(args.registry)
    release_lags = registry_release_lags(registry)
    results = expanding_window_backtest(
        monthly,
        target,
        min_train_quarters=args.min_train_quarters,
        target_transform=args.target_transform,
        nowcast_lag_days=args.nowcast_lag_days,
        release_lags=release_lags,
    )
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    results.to_csv("data/processed/backtest_results.csv", index=False)
    write_report_artifacts(monthly, target, results, registry=registry)
    print(metric_table(results).to_string(index=False))


if __name__ == "__main__":
    main()
