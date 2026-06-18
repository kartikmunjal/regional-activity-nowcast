"""Data access, provenance, caching, and point-in-time transforms."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests
import yaml

from .env import load_local_env


load_local_env()

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


@dataclass(frozen=True)
class RegistrySeries:
    name: str
    source: str
    state: str
    series_id: str
    frequency: str
    release_lag_days: int
    transform: str = "level"
    expected_sign: str | None = None


DEFAULT_RELEASE_LAGS = {
    "fred_monthly": 21,
    "fred_weekly": 7,
    "census_monthly": 30,
    "bea_quarterly": 90,
    "bls_monthly": 21,
}

TARGET_TRANSFORMS = {"level", "qoq_ann", "yoy"}


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_series_registry(path: str | Path = "config/series_registry.yml") -> dict:
    """Load auditable source metadata for indicators and targets."""
    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"Series registry not found: {registry_path}")
    return yaml.safe_load(registry_path.read_text(encoding="utf-8"))


def registry_release_lags(registry: dict) -> dict[str, int]:
    """Map indicator column names to release lags from the registry."""
    lags: dict[str, int] = {}
    for item in registry.get("indicators", []):
        name = item.get("name")
        if name:
            lags[name] = int(item.get("release_lag_days", DEFAULT_RELEASE_LAGS.get("fred_monthly", 21)))
    return lags


def registry_specs(registry: dict, states: list[str] | None = None) -> list[SeriesSpec]:
    """Convert verified registry rows with explicit series IDs into SeriesSpec objects."""
    wanted_states = set(states or [])
    specs = []
    for item in registry.get("indicators", []):
        series_by_state = item.get("series_by_state") or {}
        for state, series_id in series_by_state.items():
            if wanted_states and state not in wanted_states:
                continue
            if item.get("verified") is not True:
                continue
            specs.append(
                SeriesSpec(
                    source=item.get("source", ""),
                    series_id=series_id,
                    frequency=item.get("frequency", "monthly"),
                    release_lag_days=int(item.get("release_lag_days", 21)),
                    transform=item.get("transform", "level"),
                    description=f"{state}:{item.get('name', series_id)}",
                )
            )
    return specs


def registry_series(registry: dict, states: list[str] | None = None, source: str | None = None) -> list[RegistrySeries]:
    """Return verified registry rows with state/name metadata preserved."""
    wanted_states = set(states or [])
    rows: list[RegistrySeries] = []
    for item in registry.get("indicators", []):
        if source and item.get("source") != source:
            continue
        if item.get("verified") is not True:
            continue
        for state, series_id in (item.get("series_by_state") or {}).items():
            if wanted_states and state not in wanted_states and state != "US":
                continue
            rows.append(
                RegistrySeries(
                    name=item.get("name", series_id),
                    source=item.get("source", ""),
                    state=state,
                    series_id=series_id,
                    frequency=item.get("frequency", "monthly"),
                    release_lag_days=int(item.get("release_lag_days", 21)),
                    transform=item.get("transform", "level"),
                    expected_sign=item.get("expected_sign"),
                )
            )
    return rows


def verify_registry(registry: dict, states: list[str] | None = None) -> pd.DataFrame:
    """Verify registry IDs against provider metadata where API support exists."""
    rows = []
    wanted_states = set(states or [])
    fred_ids: list[str] = []
    id_to_meta: dict[str, tuple[str, str]] = {}
    for item in registry.get("indicators", []):
        if item.get("source") != "FRED":
            continue
        for state, series_id in (item.get("series_by_state") or {}).items():
            if wanted_states and state not in wanted_states:
                continue
            fred_ids.append(series_id)
            id_to_meta[series_id] = (item.get("name", ""), state)
    fred_status = verify_fred_series(fred_ids) if fred_ids else {}
    for series_id, ok in fred_status.items():
        name, state = id_to_meta[series_id]
        rows.append({"source": "FRED", "state": state, "series": name, "series_id": series_id, "verified": ok})
    for item in registry.get("indicators", []):
        if item.get("source") == "FRED":
            continue
        rows.append(
            {
                "source": item.get("source"),
                "state": ",".join(sorted((item.get("series_by_state") or {}).keys())) or "ALL",
                "series": item.get("name"),
                "series_id": "",
                "verified": bool(item.get("verified")),
            }
        )
    return pd.DataFrame(rows)


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

    out: dict[str, bool] = {}
    for series_id in series_ids:
        try:
            response = requests.get(
                "https://api.stlouisfed.org/fred/series",
                params={"series_id": series_id, "api_key": key, "file_type": "json"},
                timeout=30,
            )
            out[series_id] = response.ok and bool(response.json().get("seriess"))
        except Exception:
            out[series_id] = False
    return out


def _fetch_fred_observations(series_id: str, start: str, end: str, api_key: str) -> pd.Series:
    response = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start,
            "observation_end": end,
        },
        timeout=30,
    )
    response.raise_for_status()
    observations = response.json().get("observations", [])
    frame = pd.DataFrame(observations)
    if frame.empty:
        return pd.Series(dtype=float, name=series_id)
    values = pd.to_numeric(frame["value"].replace(".", np.nan), errors="coerce")
    series = pd.Series(values.to_numpy(), index=pd.to_datetime(frame["date"]), name=series_id)
    return series


def fetch_fred_series(specs: list[SeriesSpec], start: str, end: str) -> pd.DataFrame:
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY is required. See README for key setup.")
    verification = verify_fred_series([spec.series_id for spec in specs], key)
    missing = [sid for sid, ok in verification.items() if not ok]
    if missing:
        raise RuntimeError(f"FRED series failed verification: {missing}")

    frames = []
    for spec in specs:
        s = _fetch_fred_observations(spec.series_id, start, end, key)
        frames.append(s.rename(spec.series_id))
    frame = pd.concat(frames, axis=1).sort_index()
    frame.index.name = "date"
    cache_frame(frame, "fred", "verified_series")
    return frame


def fetch_fred_registry_panel(registry: dict, states: list[str], start: str, end: str) -> pd.DataFrame:
    """Fetch verified FRED registry rows and return a state/date indicator panel."""
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY is required. See README for key setup.")
    rows = registry_series(registry, states=states, source="FRED")
    if not rows:
        return pd.DataFrame(columns=["date", "state"])
    verification = verify_fred_series([row.series_id for row in rows], key)
    missing = [sid for sid, ok in verification.items() if not ok]
    if missing:
        raise RuntimeError(f"FRED series failed verification: {missing}")

    fetched: dict[str, pd.Series] = {}
    for row in rows:
        series = _fetch_fred_observations(row.series_id, start, end, key)
        series.index = pd.to_datetime(series.index)
        if row.frequency == "weekly":
            series = series.resample("ME").mean()
        else:
            series = series.resample("ME").last()
        fetched[row.series_id] = series.rename(row.series_id)
    raw = pd.concat(fetched.values(), axis=1).sort_index()
    raw.index.name = "date"
    cache_frame(raw, "fred", "registry_indicator_raw")

    pieces = []
    for state in states:
        state_frame = pd.DataFrame({"date": raw.index, "state": state})
        for row in rows:
            if row.state not in {state, "US"}:
                continue
            state_frame[row.name] = raw[row.series_id].to_numpy()
        pieces.append(state_frame)
    panel = pd.concat(pieces, ignore_index=True).sort_values(["state", "date"])
    cache_frame(panel.set_index("date"), "fred", "registry_indicator_panel")
    return panel


def fetch_live_registry_data(registry: dict, states: list[str], start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch the verified live-data pilot panel from public APIs."""
    start_year = pd.Timestamp(start).year
    end_year = pd.Timestamp(end).year
    monthly = fetch_fred_registry_panel(registry, states, start, end)
    if monthly.empty or len([c for c in monthly.columns if c not in {"date", "state"}]) == 0:
        raise RuntimeError("No verified FRED indicators were fetched. Populate and verify config/series_registry.yml first.")
    target = fetch_bea_state_gdp(start_year, end_year, states)
    target = target[(target["date"] >= pd.Timestamp(start)) & (target["date"] <= pd.Timestamp(end))]
    return monthly, target


def fetch_fred_series_as_of(specs: list[SeriesSpec], start: str, end: str, as_of: str) -> pd.DataFrame:
    """Fetch FRED/ALFRED observations as known on a vintage date where available."""
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
        if not hasattr(fred, "get_series_as_of_date"):
            raise RuntimeError("Installed fredapi version does not expose get_series_as_of_date.")
        vintages = fred.get_series_as_of_date(spec.series_id, as_of)
        if isinstance(vintages, pd.DataFrame):
            date_col = "date" if "date" in vintages.columns else vintages.columns[0]
            value_col = "value" if "value" in vintages.columns else vintages.columns[-1]
            vintage = vintages.assign(date=pd.to_datetime(vintages[date_col])).set_index("date")[value_col].astype(float)
        else:
            vintage = pd.Series(vintages)
            vintage.index = pd.to_datetime(vintage.index)
        vintage = vintage[(vintage.index >= pd.Timestamp(start)) & (vintage.index <= pd.Timestamp(end))]
        frames.append(vintage.rename(spec.series_id))
    frame = pd.concat(frames, axis=1).sort_index()
    frame.index.name = "date"
    cache_frame(frame, "fred_alfred", f"verified_series_as_of_{as_of}")
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
        payload = response.json()
        results = payload.get("BEAAPI", {}).get("Results", {})
        if "Data" not in results:
            error = results.get("Error") or payload.get("BEAAPI", {}).get("Error") or "Unknown BEA API error"
            raise RuntimeError(f"BEA state GDP fetch failed for {state}: {error}")
        data = results["Data"]
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
        formations = 40 + 0.7 * factor + rng.normal(0, 0.5, len(monthly_dates))
        national_activity = 100 + np.cumsum(rng.normal(0, 0.18, len(monthly_dates)))
        for dt, pay, ci, clm, prm, frm, nat in zip(monthly_dates, payroll, coincident, claims, permits, formations, national_activity):
            indicators.append(
                {
                    "date": dt,
                    "state": state,
                    "payroll": pay,
                    "coincident": ci,
                    "claims": clm,
                    "permits": prm,
                    "business_formations": frm,
                    "national_activity": nat,
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


def apply_indicator_transforms(panel: pd.DataFrame, registry: dict | None = None) -> pd.DataFrame:
    """Apply registry transforms in a state-local, no-lookahead way."""
    if not registry:
        return panel.copy()
    transform_by_name = {item.get("name"): item.get("transform", "level") for item in registry.get("indicators", [])}
    out = panel.sort_values(["state", "date"]).copy()
    for col, transform in transform_by_name.items():
        if col not in out.columns or transform in {None, "level"}:
            continue
        grouped = out.groupby("state")[col]
        if transform == "pct_change":
            out[col] = grouped.pct_change() * 100
        elif transform == "diff":
            out[col] = grouped.diff()
        elif transform == "log_diff":
            out[col] = grouped.transform(lambda s: np.log(s.where(s > 0)).diff() * 100)
        else:
            raise ValueError(f"Unsupported transform {transform!r} for indicator {col!r}")
    return out


def availability_matrix(panel: pd.DataFrame, as_of: str | pd.Timestamp, release_lags: dict[str, int] | None = None) -> pd.DataFrame:
    """Boolean observation availability by row/series for a forecast origin."""
    lags = release_lags or {}
    as_of_ts = pd.Timestamp(as_of)
    value_cols = [c for c in panel.columns if c not in {"date", "state"}]
    rows = panel[["date", "state"]].copy()
    for col in value_cols:
        lag = int(lags.get(col, DEFAULT_RELEASE_LAGS.get("fred_monthly", 21)))
        rows[col] = pd.to_datetime(panel["date"]) + pd.to_timedelta(lag, unit="D") <= as_of_ts
    return rows


def target_for_model(target: pd.DataFrame, transform: str = "level") -> pd.DataFrame:
    """Create the modeling target without contaminating the stored official level."""
    if transform not in TARGET_TRANSFORMS:
        raise ValueError(f"Unknown target transform {transform!r}; expected one of {sorted(TARGET_TRANSFORMS)}")
    out = target.sort_values(["state", "date"]).copy()
    if transform == "level":
        out["target_value"] = out["real_gdp"]
    elif transform == "qoq_ann":
        growth = out.groupby("state")["real_gdp"].pct_change()
        out["target_value"] = 100 * ((1 + growth) ** 4 - 1)
    elif transform == "yoy":
        out["target_value"] = 100 * out.groupby("state")["real_gdp"].pct_change(4)
    out["target_transform"] = transform
    return out.dropna(subset=["target_value"]).reset_index(drop=True)


def data_quality_report(monthly_panel: pd.DataFrame, target: pd.DataFrame, release_lags: dict[str, int] | None = None) -> pd.DataFrame:
    """Basic checks that should be inspected before trusting model output."""
    rows = []
    feature_cols = [c for c in monthly_panel.columns if c not in {"date", "state"}]
    for state, group in monthly_panel.groupby("state"):
        for col in feature_cols:
            values = group[col]
            z = (values - values.mean()) / values.std(ddof=0) if values.std(ddof=0) else values * 0
            rows.append(
                {
                    "state": state,
                    "series": col,
                    "observations": int(values.notna().sum()),
                    "missing_rate": float(values.isna().mean()),
                    "duplicate_dates": int(group.duplicated(["date"]).sum()),
                    "large_zscore_count": int((z.abs() > 5).sum()),
                    "release_lag_days": int((release_lags or {}).get(col, DEFAULT_RELEASE_LAGS["fred_monthly"])),
                }
            )
    for state, group in target.groupby("state"):
        rows.append(
            {
                "state": state,
                "series": "real_gdp",
                "observations": int(group["real_gdp"].notna().sum()),
                "missing_rate": float(group["real_gdp"].isna().mean()),
                "duplicate_dates": int(group.duplicated(["date"]).sum()),
                "large_zscore_count": 0,
                "release_lag_days": DEFAULT_RELEASE_LAGS["bea_quarterly"],
            }
        )
    return pd.DataFrame(rows)
