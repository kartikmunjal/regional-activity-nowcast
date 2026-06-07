#!/usr/bin/env python3
"""Fetch verified public data or create a synthetic smoke-test fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from regional_activity_nowcast.data import fetch_bea_state_gdp, make_synthetic_panel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--states", nargs="+", default=["CA"])
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--synthetic", action="store_true", help="Create deterministic offline fixture data.")
    args = parser.parse_args()

    if args.synthetic:
        monthly, target = make_synthetic_panel(args.states, args.start, args.end)
    else:
        raise SystemExit(
            "Live FRED/Census indicator fetches require confirmed series mapping for each requested state. "
            "Use --synthetic for the smoke fixture, or extend data.py with verified SeriesSpec entries."
        )

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    monthly.to_csv("data/processed/monthly_indicators.csv", index=False)
    target.to_csv("data/processed/quarterly_gdp.csv", index=False)
    print("Wrote data/processed/monthly_indicators.csv and data/processed/quarterly_gdp.csv")


if __name__ == "__main__":
    main()

