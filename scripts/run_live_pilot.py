#!/usr/bin/env python3
"""Run the Phase 4 verified live-data pilot once registry IDs are populated."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from regional_activity_nowcast.data import apply_indicator_transforms, fetch_live_registry_data, load_series_registry, verify_registry
from regional_activity_nowcast.evaluate import expanding_window_backtest, metric_table, write_report_artifacts
from regional_activity_nowcast.research import FindingConfig, write_research_findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="config/series_registry.yml")
    parser.add_argument("--pilot-states", default="config/pilot_states.yml")
    parser.add_argument("--states", nargs="*", default=None)
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--target-transform", choices=["level", "qoq_ann", "yoy"], default="qoq_ann")
    parser.add_argument("--min-train-quarters", type=int, default=12)
    parser.add_argument("--nowcast-lag-days", type=int, default=45)
    parser.add_argument("--placebo-permutations", type=int, default=100)
    args = parser.parse_args()

    registry = load_series_registry(args.registry)
    pilot = yaml.safe_load(Path(args.pilot_states).read_text(encoding="utf-8"))
    states = args.states or [row["state"] for row in pilot["states"]]
    verification = verify_registry(registry, states=states)
    Path("report").mkdir(parents=True, exist_ok=True)
    verification.to_csv("report/registry_verification.csv", index=False)
    fred_verification = verification[verification["source"] == "FRED"]
    if fred_verification.empty or not fred_verification["verified"].all():
        raise SystemExit("FRED registry verification failed or no verified FRED rows were found. See report/registry_verification.csv.")

    monthly_raw, target = fetch_live_registry_data(registry, states, args.start, args.end)
    monthly = apply_indicator_transforms(monthly_raw, registry)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    monthly_raw.to_csv("data/processed/monthly_indicators_raw_live.csv", index=False)
    monthly.to_csv("data/processed/monthly_indicators.csv", index=False)
    target.to_csv("data/processed/quarterly_gdp.csv", index=False)

    results = expanding_window_backtest(
        monthly,
        target,
        min_train_quarters=args.min_train_quarters,
        target_transform=args.target_transform,
        nowcast_lag_days=args.nowcast_lag_days,
    )
    results.to_csv("data/processed/backtest_results.csv", index=False)
    write_report_artifacts(monthly, target, results, registry=registry)
    write_research_findings(
        monthly,
        target,
        config=FindingConfig(target_transform=args.target_transform, placebo_permutations=args.placebo_permutations),
        data_label="verified public data pilot",
        registry=registry,
    )
    print(metric_table(results).to_string(index=False))


if __name__ == "__main__":
    main()
