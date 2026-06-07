"""Economic activity index estimators."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def _feature_columns(panel: pd.DataFrame) -> list[str]:
    return [c for c in panel.columns if c not in {"date", "state"}]


def standardized_composite(panel: pd.DataFrame, invert: set[str] | None = None) -> pd.DataFrame:
    """Transparent baseline: within-state z-scores averaged across indicators."""
    invert = invert or {"claims", "unemployment_claims"}
    features = _feature_columns(panel)
    pieces = []
    for state, group in panel.sort_values("date").groupby("state"):
        z = group[features].astype(float)
        z = (z - z.mean()) / z.std(ddof=0).replace(0, np.nan)
        for col in set(features).intersection(invert):
            z[col] = -z[col]
        composite = z.mean(axis=1, skipna=True)
        pieces.append(pd.DataFrame({"date": group["date"].values, "state": state, "composite_index": composite.values}))
    return pd.concat(pieces, ignore_index=True)


def dynamic_factor_index(panel: pd.DataFrame, factors: int = 1) -> pd.DataFrame:
    """Estimate a mixed-frequency-capable DFM via statsmodels DynamicFactorMQ."""
    from statsmodels.tsa.statespace.dynamic_factor_mq import DynamicFactorMQ

    features = _feature_columns(panel)
    outputs = []
    for state, group in panel.sort_values("date").groupby("state"):
        y = group.set_index("date")[features].astype(float).asfreq("ME")
        if len(y.dropna(how="all")) < max(12, len(features) * 3):
            continue
        y_scaled = pd.DataFrame(StandardScaler().fit_transform(y), index=y.index, columns=y.columns)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = DynamicFactorMQ(y_scaled, factors=factors, factor_orders=1, idiosyncratic_ar1=True)
            result = model.fit(disp=False, maxiter=200)
        factor = result.factors.filtered.iloc[:, 0]
        outputs.append(pd.DataFrame({"date": factor.index, "state": state, "dfm_index": factor.values}))
    if not outputs:
        return pd.DataFrame(columns=["date", "state", "dfm_index"])
    return pd.concat(outputs, ignore_index=True)


def dynamic_factor_diagnostics(panel: pd.DataFrame, factors: int = 1) -> pd.DataFrame:
    """Fit the DFM by state and return convergence diagnostics."""
    from statsmodels.tsa.statespace.dynamic_factor_mq import DynamicFactorMQ

    features = _feature_columns(panel)
    rows = []
    for state, group in panel.sort_values("date").groupby("state"):
        y = group.set_index("date")[features].astype(float).asfreq("ME")
        usable = len(y.dropna(how="all"))
        row = {"state": state, "observations": int(usable), "features": len(features)}
        if usable < max(12, len(features) * 3):
            row.update({"converged": False, "iterations": 0, "llf": np.nan, "warning_count": 0, "status": "insufficient_history"})
            rows.append(row)
            continue
        y_scaled = pd.DataFrame(StandardScaler().fit_transform(y), index=y.index, columns=y.columns)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                model = DynamicFactorMQ(y_scaled, factors=factors, factor_orders=1, idiosyncratic_ar1=True)
                result = model.fit(disp=False, maxiter=200)
                mle = getattr(result, "mle_retvals", {}) or {}
                row.update(
                    {
                        "converged": bool(mle.get("converged", len(caught) == 0)),
                        "iterations": int(mle.get("iterations", mle.get("iter", 200))),
                        "llf": float(getattr(result, "llf", np.nan)),
                        "warning_count": int(len(caught)),
                        "status": "fit",
                    }
                )
            except Exception as exc:
                row.update(
                    {
                        "converged": False,
                        "iterations": 0,
                        "llf": np.nan,
                        "warning_count": int(len(caught)),
                        "status": f"failed:{type(exc).__name__}",
                    }
                )
        rows.append(row)
    return pd.DataFrame(rows)


def compare_indexes(composite: pd.DataFrame, dfm: pd.DataFrame, official: pd.DataFrame | None = None) -> pd.DataFrame:
    merged = composite.merge(dfm, on=["date", "state"], how="outer")
    if official is not None:
        official_q = official.rename(columns={"real_gdp": "official_real_gdp"})
        merged = merged.merge(official_q, on=["date", "state"], how="left")
    rows = []
    for state, group in merged.groupby("state"):
        row = {"state": state}
        if {"composite_index", "dfm_index"}.issubset(group.columns):
            row["composite_dfm_corr"] = group["composite_index"].corr(group["dfm_index"])
        if "official_real_gdp" in group:
            quarterly = group.dropna(subset=["official_real_gdp"])
            row["composite_gdp_corr"] = quarterly["composite_index"].corr(quarterly["official_real_gdp"])
            row["dfm_gdp_corr"] = quarterly["dfm_index"].corr(quarterly["official_real_gdp"])
        rows.append(row)
    return pd.DataFrame(rows)
