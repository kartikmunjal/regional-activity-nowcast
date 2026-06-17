#!/usr/bin/env python3
"""Generate Phase 3 robustness and falsification checks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from regional_activity_nowcast.data import apply_indicator_transforms, load_series_registry
from regional_activity_nowcast.research import robustness_grid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monthly", default="data/processed/monthly_indicators.csv")
    parser.add_argument("--target", default="data/processed/quarterly_gdp.csv")
    parser.add_argument("--registry", default="config/series_registry.yml")
    parser.add_argument("--target-transforms", nargs="+", default=["level", "qoq_ann", "yoy"])
    parser.add_argument("--nowcast-lags", nargs="+", type=int, default=[15, 45, 75])
    parser.add_argument("--min-train-quarters", type=int, default=12)
    parser.add_argument("--out", default="report/robustness_grid.csv")
    args = parser.parse_args()

    registry = load_series_registry(args.registry)
    monthly = apply_indicator_transforms(pd.read_csv(args.monthly, parse_dates=["date"]), registry)
    target = pd.read_csv(args.target, parse_dates=["date"])
    grid = robustness_grid(
        monthly,
        target,
        target_transforms=args.target_transforms,
        nowcast_lags=args.nowcast_lags,
        min_train_quarters=args.min_train_quarters,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    grid.to_csv(args.out, index=False)
    print(grid.sort_values(["target_transform", "nowcast_lag_days", "rmse"]).to_string(index=False))


if __name__ == "__main__":
    main()

