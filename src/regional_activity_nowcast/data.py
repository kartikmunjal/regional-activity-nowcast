"""Data access, provenance, caching, and point-in-time transforms."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

STATE_FIPS = {
    "AL": "01",
    "AK": "02",
    "AZ": "04",
    "AR": "05",
    "CA": "06",
    "CO": "08",
    "CT": "09",
    "DE": "10",
    "FL": "12",
    "GA": "13",
    "HI": "15",
    "ID": "16",
    "IL": "17",
    "IN": "18",
    "IA": "19",
    "KS": "20",
    "KY": "21",
    "LA": "22",
    "ME": "23",
    "MD": "24",
    "MA": "25",
    "MI": "26",
    "MN": "27",
    "MS": "28",
    "MO": "29",
    "MT": "30",
    "NE": "31",
    "NV": "32",
    "NH": "33",
    "NJ": "34",
    "NM": "35",
    "NY": "36",
    "NC": "37",
    "ND": "38",
    "OH": "39",
    "OK": "40",
    "OR": "41",
    "PA": "42",
    "RI": "44",
    "SC": "45",
    "SD": "46",
    "TN": "47",
    "TX": "48",
    "UT": "49",
    "VT": "50",
    "VA": "51",
    "WA": "53",
    "WV": "54",
    "WI": "55",
    "WY": "56",
}


@dataclass(frozen=True)
class SeriesSpec:
    source: str
    series_id: str
    frequency: str
    release_lag_days: int
    transform: str = "level"
    description: str = ""


DEFAULT_RELEASE_LAGS = {
    "fred_monthly": 21,
    "fred_weekly": 7,
    "census_monthly": 30,
    "bea_quarterly": 90,
    "bls_monthly": 21,
}


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def cache_frame(frame: pd.DataFrame, source: str, name: str) -> Path:
    ensure_dirs()
    stamp = date.today().isoformat()
    path = RAW_DIR / f"{stamp}_{source}_{name}.csv"
    frame.to_csv(path, index=True)
    meta = {
        "source": source,
        "name": name,
        "fetch_date": stamp,
        "rows": int(len(frame)),
        "columns": list(map(str, frame.columns)),
    }
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return path


def verify_fred_series(series_ids: Iterable[str], api_key: str | None = None) -> dict[str, bool]:
    """Confirm FRED series IDs before fetching values."""
    key = api_key or os.getenv("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY is required to verify FRED series IDs.")
    try:
        from fredapi import Fred
    except ImportError as exc:
        raise RuntimeError("Install fredapi before fetching FRED data.") from exc

    fred = Fred(api_key=key)
    out: dict[str, bool] = {}
    for series_id in series_ids:
        try:
            fred.get_series_info(series_id)
            out[series_id] = True
        except Exception:
            out[series_id] = False
    return out


def fetch_fred_series(specs: list[SeriesSpec], start: str, end: str) -> pd.DataFrame:
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY is required. See README for key setup.")
    verification = verify_fred_series([spec.series_id for spec in specs], key)
    missing = [sid for sid, ok in verification.items() if not ok]
    if missing:
        raise RuntimeError(f"FRED series failed verification: {missing}")

    from fredapi import Fred

    fred = Fred(api_key=key)
    frames = []
    for spec in specs:
        s = fred.get_series(spec.series_id, observation_start=start, observation_end=end)
        frames.append(s.rename(spec.series_id))
    frame = pd.concat(frames, axis=1).sort_index()
    frame.index.name = "date"
    cache_frame(frame, "fred", "verified_series")
    return frame


def fetch_census_json(path: str, params: dict[str, str], name: str) -> pd.DataFrame:
    key = os.getenv("CENSUS_API_KEY")
    if key:
        params = {**params, "key": key}
    url = f"https://api.census.gov/data/{path}"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    frame = pd.DataFrame(payload[1:], columns=payload[0])
    cache_frame(frame, "census", name)
    return frame


def fetch_bea_state_gdp(start_year: int, end_year: int, states: list[str]) -> pd.DataFrame:
    key = os.getenv("BEA_API_KEY")
    if not key:
        raise RuntimeError("BEA_API_KEY is required. See README for key setup.")
    rows = []
    for state in states:
        params = {
            "UserID": key,
            "method": "GetData",
            "datasetname": "Regional",
            "TableName": "SQGDP9",
            "LineCode": "1",
            "GeoFIPS": STATE_FIPS[state],
            "Year": f"{start_year},{end_year}",
            "Frequency": "Q",
            "ResultFormat": "JSON",
        }
        response = requests.get("https://apps.bea.gov/api/data", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()["BEAAPI"]["Results"]["Data"]
        for item in data:
            rows.append(
                {
                    "date": pd.Period(item["TimePeriod"], freq="Q").to_timestamp("Q"),
                    "state": state,
                    "real_gdp": float(str(item["DataValue"]).replace(",", "")),
                }
            )
    frame = pd.DataFrame(rows).sort_values(["state", "date"])
    cache_frame(frame.set_index("date"), "bea", "state_real_gdp")
    return frame


def make_synthetic_panel(states: list[str], start: str, end: str, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Small deterministic fixture with the same shape as the public-data pipeline."""
    rng = np.random.default_rng(seed)
    monthly_dates = pd.date_range(start=start, end=end, freq="ME")
    q_dates = pd.date_range(start=start, end=end, freq="QE")
    indicators = []
    targets = []
    for state_idx, state in enumerate(states):
        factor = np.cumsum(rng.normal(0, 0.35, len(monthly_dates))) + state_idx * 0.2
        payroll = 100 + factor + rng.normal(0, 0.2, len(monthly_dates))
        coincident = 100 + 1.3 * factor + rng.normal(0, 0.25, len(monthly_dates))
        claims = 50 - 1.2 * factor + rng.normal(0, 0.3, len(monthly_dates))
        permits = 75 + 0.5 * factor + rng.normal(0, 0.8, len(monthly_dates))
        for dt, pay, ci, clm, prm in zip(monthly_dates, payroll, coincident, claims, permits):
            indicators.append(
                {
                    "date": dt,
                    "state": state,
                    "payroll": pay,
                    "coincident": ci,
                    "claims": clm,
                    "permits": prm,
                }
            )
        monthly = pd.Series(factor, index=monthly_dates)
        for qdt in q_dates:
            avg_factor = monthly.loc[:qdt].tail(3).mean()
            targets.append(
                {
                    "date": qdt,
                    "state": state,
                    "real_gdp": 500 + 2.0 * avg_factor + rng.normal(0, 0.5),
                }
            )
    indicators_df = pd.DataFrame(indicators)
    targets_df = pd.DataFrame(targets)
    cache_frame(indicators_df.set_index("date"), "synthetic", "monthly_indicators")
    cache_frame(targets_df.set_index("date"), "synthetic", "quarterly_gdp")
    return indicators_df, targets_df


def apply_release_lags(panel: pd.DataFrame, as_of: str | pd.Timestamp, release_lags: dict[str, int] | None = None) -> pd.DataFrame:
    """Drop observations not available as of a nowcast date under lag assumptions."""
    lags = release_lags or {}
    as_of_ts = pd.Timestamp(as_of)
    out = panel.copy()
    value_cols = [c for c in out.columns if c not in {"date", "state"}]
    for col in value_cols:
        lag = int(lags.get(col, DEFAULT_RELEASE_LAGS.get("fred_monthly", 21)))
        released = pd.to_datetime(out["date"]) + pd.to_timedelta(lag, unit="D")
        out.loc[released > as_of_ts, col] = np.nan
    return out

