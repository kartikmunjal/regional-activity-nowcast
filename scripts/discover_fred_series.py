#!/usr/bin/env python3
"""Search FRED for candidate series IDs to populate the verified registry."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests
import yaml


QUERY_TEMPLATES = {
    "payroll": "{state} nonfarm payroll employment seasonally adjusted",
    "claims": "{state} continued claims unemployment insurance",
    "coincident": "{state} coincident index Philadelphia Fed",
    "national_activity": "US coincident index national activity monthly",
}


def fred_search(query: str, limit: int, api_key: str) -> list[dict]:
    params = {
        "api_key": api_key,
        "file_type": "json",
        "search_text": query,
        "limit": limit,
        "order_by": "search_rank",
        "sort_order": "desc",
    }
    response = requests.get("https://api.stlouisfed.org/fred/series/search", params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("seriess", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-states", default="config/pilot_states.yml")
    parser.add_argument("--indicators", nargs="+", default=["payroll", "claims", "coincident", "national_activity"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--out", default="report/fred_series_candidates.csv")
    args = parser.parse_args()

    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise SystemExit("FRED_API_KEY is required for discovery.")
    pilot = yaml.safe_load(Path(args.pilot_states).read_text(encoding="utf-8"))
    states = [row["state"] for row in pilot["states"]]
    rows = []
    for indicator in args.indicators:
        template = QUERY_TEMPLATES[indicator]
        search_states = ["US"] if indicator == "national_activity" else states
        for state in search_states:
            query = template.format(state=state)
            for rank, item in enumerate(fred_search(query, args.limit, api_key), start=1):
                rows.append(
                    {
                        "indicator": indicator,
                        "state": state,
                        "rank": rank,
                        "query": query,
                        "series_id": item.get("id"),
                        "title": item.get("title"),
                        "frequency": item.get("frequency"),
                        "seasonal_adjustment": item.get("seasonal_adjustment"),
                        "units": item.get("units"),
                        "observation_start": item.get("observation_start"),
                        "observation_end": item.get("observation_end"),
                        "popularity": item.get("popularity"),
                        "notes": item.get("notes", "")[:500],
                    }
                )
    out = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {args.out} with {len(out)} candidates")


if __name__ == "__main__":
    main()
