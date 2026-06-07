"""Bridge, DFM, and benchmark nowcasting models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler

from .data import apply_release_lags
from .index import dynamic_factor_index, standardized_composite


def quarterly_features(
    monthly_panel: pd.DataFrame,
    as_of: str | pd.Timestamp | None = None,
    release_lags: dict[str, int] | None = None,
) -> pd.DataFrame:
    panel = monthly_panel if as_of is None else apply_release_lags(monthly_panel, as_of, release_lags)
    value_cols = [c for c in panel.columns if c not in {"date", "state"}]
    rows = []
    for state, group in panel.groupby("state"):
        q = group.set_index("date")[value_cols].resample("QE").mean()
        q["state"] = state
        rows.append(q.reset_index())
    return pd.concat(rows, ignore_index=True)


def _fill_from_training(train_x: pd.DataFrame, test_x: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    med = train_x.median(numeric_only=True).fillna(0)
    return train_x.fillna(med), test_x.fillna(med)


def bridge_nowcast(train_x: pd.DataFrame, train_y: pd.Series, test_x: pd.DataFrame) -> np.ndarray:
    scaler = StandardScaler()
    x_train, x_test = _fill_from_training(train_x, test_x)
    model = Ridge(alpha=1.0)
    model.fit(scaler.fit_transform(x_train), train_y)
    return model.predict(scaler.transform(x_test))


def dfm_nowcast(train_monthly: pd.DataFrame, train_target: pd.DataFrame, test_monthly: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    combined = test_monthly.copy()
    try:
        idx = dynamic_factor_index(combined)
        q_idx = idx.set_index("date").groupby("state")["dfm_index"].resample("QE").mean().reset_index()
        train = train_target.merge(q_idx, on=["date", "state"], how="inner")
        test = test_key.merge(q_idx, on=["date", "state"], how="left")
        if train["dfm_index"].notna().sum() < 6 or test["dfm_index"].isna().any():
            raise ValueError("Insufficient DFM factor coverage.")
        reg = LinearRegression()
        reg.fit(train[["dfm_index"]], train["target_value"])
        return reg.predict(test[["dfm_index"]])
    except Exception:
        comp = standardized_composite(combined)
        q_idx = comp.set_index("date").groupby("state")["composite_index"].resample("QE").mean().reset_index()
        train = train_target.merge(q_idx, on=["date", "state"], how="inner")
        test = test_key.merge(q_idx, on=["date", "state"], how="left")
        reg = LinearRegression()
        reg.fit(train[["composite_index"]].fillna(0), train["target_value"])
        return reg.predict(test[["composite_index"]].fillna(0))


def random_walk_forecast(train_target: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    out = []
    for _, row in test_key.iterrows():
        history = train_target[train_target["state"] == row["state"]].sort_values("date")
        out.append(float(history["target_value"].iloc[-1]))
    return np.array(out)


def ar1_forecast(train_target: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    out = []
    for _, row in test_key.iterrows():
        y = train_target[train_target["state"] == row["state"]].sort_values("date")["target_value"]
        if len(y) < 4:
            out.append(float(y.iloc[-1]))
            continue
        lag = y.shift(1).dropna()
        cur = y.loc[lag.index]
        model = LinearRegression().fit(lag.to_numpy().reshape(-1, 1), cur.to_numpy())
        out.append(float(model.predict(np.array([[y.iloc[-1]]]))[0]))
    return np.array(out)


def state_mean_forecast(train_target: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    """State-specific expanding mean benchmark."""
    out = []
    pooled = float(train_target["target_value"].mean())
    for _, row in test_key.iterrows():
        history = train_target[train_target["state"] == row["state"]]["target_value"]
        out.append(float(history.mean()) if len(history) else pooled)
    return np.array(out)


def pooled_mean_forecast(train_target: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    """Cross-state unconditional mean benchmark."""
    return np.repeat(float(train_target["target_value"].mean()), len(test_key))


def peer_average_forecast(train_target: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    """Average latest target from all other states, falling back to own latest value."""
    out = []
    latest = train_target.sort_values("date").groupby("state").tail(1)
    for _, row in test_key.iterrows():
        peers = latest[latest["state"] != row["state"]]
        if peers.empty:
            peers = latest[latest["state"] == row["state"]]
        out.append(float(peers["target_value"].mean()))
    return np.array(out)


def national_context_bridge(train_x: pd.DataFrame, train_y: pd.Series, test_x: pd.DataFrame) -> np.ndarray:
    """Bridge using only national context columns when present."""
    cols = [c for c in train_x.columns if c.startswith("national_")]
    if not cols:
        return np.repeat(float(train_y.mean()), len(test_x))
    return bridge_nowcast(train_x[cols], train_y, test_x[cols])
