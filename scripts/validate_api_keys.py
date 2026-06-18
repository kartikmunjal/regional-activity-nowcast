#!/usr/bin/env python3
"""Validate local public-data API keys without printing secrets."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests

from regional_activity_nowcast.env import load_local_env


def _json_or_none(response: requests.Response):
    try:
        return response.json()
    except ValueError:
        return None


def check_fred() -> dict:
    key = os.getenv("FRED_API_KEY")
    if not key:
        return {"provider": "FRED", "present": False, "active": False, "message": "missing FRED_API_KEY"}
    response = requests.get(
        "https://api.stlouisfed.org/fred/series",
        params={"series_id": "USPHCI", "api_key": key, "file_type": "json"},
        timeout=30,
    )
    payload = _json_or_none(response) or {}
    active = response.ok and bool(payload.get("seriess"))
    return {"provider": "FRED", "present": True, "active": active, "message": "ok" if active else "series lookup failed"}


def check_bea() -> dict:
    key = os.getenv("BEA_API_KEY")
    if not key:
        return {"provider": "BEA", "present": False, "active": False, "message": "missing BEA_API_KEY"}
    response = requests.get(
        "https://apps.bea.gov/api/data",
        params={
            "UserID": key,
            "method": "GetData",
            "datasetname": "Regional",
            "TableName": "SQGDP9",
            "LineCode": "1",
            "GeoFips": "06000",
            "Year": "2024",
            "Frequency": "Q",
            "ResultFormat": "JSON",
        },
        timeout=30,
    )
    payload = _json_or_none(response) or {}
    results = payload.get("BEAAPI", {}).get("Results", {})
    active = response.ok and "Data" in results
    error = results.get("Error") or payload.get("BEAAPI", {}).get("Error") or {}
    message = "ok" if active else str(error)
    return {"provider": "BEA", "present": True, "active": active, "message": message}


def check_census() -> dict:
    key = os.getenv("CENSUS_API_KEY")
    if not key:
        return {"provider": "Census", "present": False, "active": False, "message": "missing CENSUS_API_KEY"}
    response = requests.get(
        "https://api.census.gov/data/2023/acs/acs5/profile",
        params={"get": "NAME,DP03_0001E", "for": "state:06", "key": key},
        timeout=30,
    )
    payload = _json_or_none(response)
    active = response.ok and isinstance(payload, list)
    return {"provider": "Census", "present": True, "active": active, "message": "ok" if active else response.text[:200]}


def main() -> None:
    load_local_env()
    rows = [check_fred(), check_bea(), check_census()]
    out = pd.DataFrame(rows)
    Path("report").mkdir(parents=True, exist_ok=True)
    out.to_csv("report/api_key_validation.csv", index=False)
    print(out.to_string(index=False))
    if not out["active"].all():
        raise SystemExit("At least one API key is missing or inactive. See report/api_key_validation.csv.")


if __name__ == "__main__":
    main()
