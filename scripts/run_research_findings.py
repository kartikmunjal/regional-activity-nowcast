#!/usr/bin/env python3
"""Generate Phase 2 economic research findings from the current panel."""

from __future__ import annotations

import argparse

import pandas as pd

from regional_activity_nowcast.data import apply_indicator_transforms, load_series_registry
from regional_activity_nowcast.research import FindingConfig, write_research_findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monthly", default="data/processed/monthly_indicators.csv")
    parser.add_argument("--target", default="data/processed/quarterly_gdp.csv")
    parser.add_argument("--registry", default="config/series_registry.yml")
    parser.add_argument("--target-transform", choices=["level", "qoq_ann", "yoy"], default="qoq_ann")
    parser.add_argument("--max-lag-quarters", type=int, default=4)
    parser.add_argument("--clusters", type=int, default=4)
    parser.add_argument("--placebo-permutations", type=int, default=100)
    parser.add_argument("--data-label", default="synthetic fixture")
    args = parser.parse_args()

    registry = load_series_registry(args.registry)
    monthly = apply_indicator_transforms(pd.read_csv(args.monthly, parse_dates=["date"]), registry)
    target = pd.read_csv(args.target, parse_dates=["date"])
    outputs = write_research_findings(
        monthly,
        target,
        config=FindingConfig(
            target_transform=args.target_transform,
            max_lag_quarters=args.max_lag_quarters,
            n_clusters=args.clusters,
            placebo_permutations=args.placebo_permutations,
        ),
        data_label=args.data_label,
        registry=registry,
    )
    print("Generated research tables:")
    for name, frame in outputs.items():
        print(f"{name}: {len(frame)} rows")


if __name__ == "__main__":
    main()
