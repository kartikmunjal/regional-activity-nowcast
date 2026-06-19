#!/usr/bin/env python3
"""Populate the live registry with formula-based FRED state indicators."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from regional_activity_nowcast.data import load_series_registry, verify_registry


def _states_from_file(path: Path) -> list[str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [row["state"] if isinstance(row, dict) else row for row in payload["states"]]


def _series_map(indicator: str, states: list[str]) -> dict[str, str]:
    if indicator == "payroll":
        return {state: f"{state}NA" for state in states}
    if indicator == "claims":
        return {state: f"{state}CCLAIMS" for state in states}
    if indicator == "coincident":
        return {state: f"{state}PHCI" for state in states if state != "DC"}
    if indicator == "national_activity":
        return {"US": "USPHCI"}
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="config/series_registry.yml")
    parser.add_argument("--pilot-states", default="config/pilot_states.yml")
    parser.add_argument("--states-file", default=None)
    parser.add_argument("--states", nargs="*", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    out_path = Path(args.out) if args.out else registry_path
    if args.states:
        states = args.states
    else:
        states = _states_from_file(Path(args.states_file or args.pilot_states))
    registry = load_series_registry(registry_path)
    for item in registry.get("indicators", []):
        if item.get("source") != "FRED":
            continue
        series_by_state = _series_map(item.get("name", ""), states)
        if not series_by_state:
            continue
        item["series_by_state"] = series_by_state
        item["verified"] = True
    out_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    if args.verify:
        verification = verify_registry(registry, states=states)
        Path("report").mkdir(parents=True, exist_ok=True)
        verification.to_csv("report/registry_verification.csv", index=False)
        print(verification.to_string(index=False))
        failed = verification[(verification["source"] == "FRED") & (~verification["verified"])]
        if not failed.empty:
            raise SystemExit(f"FRED verification failed for {len(failed)} rows")
        pd.DataFrame(
            [
                {"indicator": item["name"], "series_by_state": item.get("series_by_state", {})}
                for item in registry.get("indicators", [])
                if item.get("source") == "FRED"
            ]
        ).to_csv("report/bootstrap_fred_registry_audit.csv", index=False)


if __name__ == "__main__":
    main()
