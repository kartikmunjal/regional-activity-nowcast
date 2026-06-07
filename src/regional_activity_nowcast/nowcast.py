"""Bridge, DFM, and benchmark nowcasting models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler

from .data import apply_release_lags
from .index import dynamic_factor_index, standardized_composite


def quarterly_features(monthly_panel: pd.DataFrame, as_of: str | pd.Timestamp | None = None) -> pd.DataFrame:
    panel = monthly_panel if as_of is None else apply_release_lags(monthly_panel, as_of)
    value_cols = [c for c in panel.columns if c not in {"date", "state"}]
    rows = []
    for state, group in panel.groupby("state"):
        q = group.set_index("date")[value_cols].resample("QE").mean()
        q["state"] = state
        rows.append(q.reset_index())
    return pd.concat(rows, ignore_index=True)


def bridge_nowcast(train_x: pd.DataFrame, train_y: pd.Series, test_x: pd.DataFrame) -> np.ndarray:
    scaler = StandardScaler()
    x_train = train_x.fillna(train_x.median(numeric_only=True))
    x_test = test_x.fillna(train_x.median(numeric_only=True))
    model = Ridge(alpha=1.0)
    model.fit(scaler.fit_transform(x_train), train_y)
    return model.predict(scaler.transform(x_test))


def dfm_nowcast(train_monthly: pd.DataFrame, train_target: pd.DataFrame, test_monthly: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    combined = pd.concat([train_monthly, test_monthly], ignore_index=True)
    try:
        idx = dynamic_factor_index(combined)
        q_idx = idx.set_index("date").groupby("state")["dfm_index"].resample("QE").mean().reset_index()
        train = train_target.merge(q_idx, on=["date", "state"], how="inner")
        test = test_key.merge(q_idx, on=["date", "state"], how="left")
        if train["dfm_index"].notna().sum() < 6 or test["dfm_index"].isna().any():
            raise ValueError("Insufficient DFM factor coverage.")
        reg = LinearRegression()
        reg.fit(train[["dfm_index"]], train["real_gdp"])
        return reg.predict(test[["dfm_index"]])
    except Exception:
        comp = standardized_composite(combined)
        q_idx = comp.set_index("date").groupby("state")["composite_index"].resample("QE").mean().reset_index()
        train = train_target.merge(q_idx, on=["date", "state"], how="inner")
        test = test_key.merge(q_idx, on=["date", "state"], how="left")
        reg = LinearRegression()
        reg.fit(train[["composite_index"]].fillna(0), train["real_gdp"])
        return reg.predict(test[["composite_index"]].fillna(0))


def random_walk_forecast(train_target: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    out = []
    for _, row in test_key.iterrows():
        history = train_target[train_target["state"] == row["state"]].sort_values("date")
        out.append(float(history["real_gdp"].iloc[-1]))
    return np.array(out)


def ar1_forecast(train_target: pd.DataFrame, test_key: pd.DataFrame) -> np.ndarray:
    out = []
    for _, row in test_key.iterrows():
        y = train_target[train_target["state"] == row["state"]].sort_values("date")["real_gdp"]
        if len(y) < 4:
            out.append(float(y.iloc[-1]))
            continue
        lag = y.shift(1).dropna()
        cur = y.loc[lag.index]
        model = LinearRegression().fit(lag.to_numpy().reshape(-1, 1), cur.to_numpy())
        out.append(float(model.predict(np.array([[y.iloc[-1]]]))[0]))
    return np.array(out)

