#!/usr/bin/env python3
"""Build composite and DFM state activity indexes."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from regional_activity_nowcast.index import compare_indexes, dynamic_factor_index, standardized_composite


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monthly", default="data/processed/monthly_indicators.csv")
    parser.add_argument("--target", default="data/processed/quarterly_gdp.csv")
    args = parser.parse_args()

    monthly = pd.read_csv(args.monthly, parse_dates=["date"])
    target = pd.read_csv(args.target, parse_dates=["date"])
    composite = standardized_composite(monthly)
    try:
        dfm = dynamic_factor_index(monthly)
    except Exception as exc:
        print(f"DFM index failed; wrote composite only. Reason: {exc}")
        dfm = pd.DataFrame(columns=["date", "state", "dfm_index"])

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("report").mkdir(parents=True, exist_ok=True)
    composite.to_csv("data/processed/composite_index.csv", index=False)
    dfm.to_csv("data/processed/dfm_index.csv", index=False)
    compare_indexes(composite, dfm, target).to_csv("report/index_comparison.csv", index=False)
    print("Wrote index outputs to data/processed/")


if __name__ == "__main__":
    main()
