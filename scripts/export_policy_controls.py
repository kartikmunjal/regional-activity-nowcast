#!/usr/bin/env python3
"""Export state-year regional controls for downstream policy-evaluation repos."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from regional_activity_nowcast.data import apply_indicator_transforms, load_series_registry
from regional_activity_nowcast.policy_controls import (
    annual_policy_controls,
    nowcast_surprises,
    policy_control_codebook,
    quarterly_activity_controls,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monthly", default="data/processed/monthly_indicators.csv")
    parser.add_argument("--target", default="data/processed/quarterly_gdp.csv")
    parser.add_argument("--backtest", default="data/processed/backtest_results.csv")
    parser.add_argument("--registry", default="config/series_registry.yml")
    parser.add_argument("--target-transform", choices=["level", "qoq_ann", "yoy"], default="qoq_ann")
    parser.add_argument("--model", default="bridge")
    parser.add_argument("--benchmark", default="ar1")
    parser.add_argument("--output-dir", default="report")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    registry = load_series_registry(args.registry)
    monthly = apply_indicator_transforms(pd.read_csv(args.monthly, parse_dates=["date"]), registry)
    target = pd.read_csv(args.target, parse_dates=["date"])
    q_controls = quarterly_activity_controls(monthly, target, target_transform=args.target_transform)
    backtest_path = Path(args.backtest)
    surprises = pd.DataFrame()
    if backtest_path.exists():
        backtest = pd.read_csv(backtest_path, parse_dates=["date", "forecast_origin"])
        surprises = nowcast_surprises(backtest, model=args.model, benchmark=args.benchmark)
    annual = annual_policy_controls(q_controls, surprises)
    q_controls.to_csv(out / "quarterly_policy_controls.csv", index=False)
    surprises.to_csv(out / "nowcast_surprises.csv", index=False)
    annual.to_csv(out / "state_year_policy_controls.csv", index=False)
    policy_control_codebook().to_csv(out / "policy_control_codebook.csv", index=False)
    print(f"Wrote {out / 'state_year_policy_controls.csv'} with {len(annual)} rows")
    if surprises.empty:
        print("No backtest surprises exported because the backtest file was not found.")


if __name__ == "__main__":
    main()
