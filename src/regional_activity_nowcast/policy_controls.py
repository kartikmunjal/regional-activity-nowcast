"""Export regional-cycle controls for policy-evaluation designs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import target_for_model
from .index import standardized_composite
from .nowcast import quarterly_features


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    return [c for c in frame.columns if c not in {"date", "state"}]


def quarterly_activity_controls(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame | None = None,
    target_transform: str = "qoq_ann",
) -> pd.DataFrame:
    """Construct state-quarter activity controls from the indicator panel."""
    q_features = quarterly_features(monthly_panel)
    composite = standardized_composite(monthly_panel)
    q_composite = (
        composite.set_index("date")
        .groupby("state")["composite_index"]
        .resample("QE")
        .mean()
        .reset_index()
    )
    controls = q_features.merge(q_composite, on=["date", "state"], how="left")
    controls = controls.sort_values(["state", "date"]).copy()
    controls = controls.replace([np.inf, -np.inf], np.nan)
    features = _feature_columns(q_features)
    controls["activity_momentum"] = controls.groupby("state")["composite_index"].diff()
    controls["activity_percentile"] = controls.groupby("state")["composite_index"].rank(pct=True)
    controls["negative_indicator_breadth"] = (
        controls.groupby("state", group_keys=False)[features]
        .apply(lambda g: (g.diff() < 0).mean(axis=1))
        .reset_index(drop=True)
    )
    if target is not None:
        y = target_for_model(target, target_transform)[["date", "state", "target_value"]]
        controls = controls.merge(y.rename(columns={"target_value": f"gdp_{target_transform}"}), on=["date", "state"], how="left")
    controls["year"] = pd.to_datetime(controls["date"]).dt.year
    controls["quarter"] = pd.to_datetime(controls["date"]).dt.quarter
    return controls


def nowcast_surprises(
    backtest_results: pd.DataFrame,
    model: str = "bridge",
    benchmark: str = "ar1",
) -> pd.DataFrame:
    """Convert backtest residuals into policy-design surprise measures.

    Positive surprises mean actual regional growth/activity exceeded the model
    forecast. The benchmark-relative fields show whether the chosen model
    improves absolute error versus a simple benchmark for the same state-quarter.
    """
    required = {"date", "state", "model", "actual", "prediction", "error"}
    missing = required - set(backtest_results.columns)
    if missing:
        raise ValueError(f"Backtest results missing required columns: {sorted(missing)}")
    work = backtest_results.copy()
    work["date"] = pd.to_datetime(work["date"])
    selected = work[work["model"] == model].copy()
    if selected.empty:
        raise ValueError(f"No backtest rows found for model `{model}`.")
    selected["activity_surprise"] = selected["actual"] - selected["prediction"]
    selected["abs_error"] = selected["error"].abs()
    base = (
        work[work["model"] == benchmark][["date", "state", "error"]]
        .rename(columns={"error": "benchmark_error"})
        .copy()
    )
    out = selected.merge(base, on=["date", "state"], how="left")
    out["benchmark_abs_error"] = out["benchmark_error"].abs()
    out["abs_error_improvement_vs_benchmark"] = out["benchmark_abs_error"] - out["abs_error"]
    out = out.replace([np.inf, -np.inf], np.nan)
    out["year"] = out["date"].dt.year
    out["quarter"] = out["date"].dt.quarter
    keep = [
        "date",
        "state",
        "year",
        "quarter",
        "model",
        "actual",
        "prediction",
        "activity_surprise",
        "abs_error",
        "benchmark_error",
        "abs_error_improvement_vs_benchmark",
        "target_transform",
        "nowcast_lag_days",
        "available_indicator_share",
    ]
    return out[[c for c in keep if c in out.columns]].sort_values(["state", "date"])


def annual_policy_controls(quarterly_controls: pd.DataFrame, surprises: pd.DataFrame | None = None) -> pd.DataFrame:
    """Aggregate quarterly controls to state-year rows for causal-policy merges."""
    controls = quarterly_controls.copy()
    controls = controls.replace([np.inf, -np.inf], np.nan)
    numeric_cols = [
        c
        for c in controls.select_dtypes(include=[np.number]).columns
        if c not in {"year", "quarter"}
    ]
    annual = controls.groupby(["state", "year"], as_index=False)[numeric_cols].mean()
    annual = annual.rename(
        columns={
            "composite_index": "avg_activity_index",
            "activity_momentum": "avg_activity_momentum",
            "activity_percentile": "avg_activity_percentile",
            "negative_indicator_breadth": "avg_negative_indicator_breadth",
        }
    )
    if surprises is not None and not surprises.empty:
        s = surprises.copy()
        s = s.replace([np.inf, -np.inf], np.nan)
        s_numeric = [
            c
            for c in s.select_dtypes(include=[np.number]).columns
            if c not in {"year", "quarter", "nowcast_lag_days"}
        ]
        surprise_annual = s.groupby(["state", "year"], as_index=False)[s_numeric].mean()
        surprise_annual = surprise_annual.rename(
            columns={
                "activity_surprise": "avg_activity_surprise",
                "abs_error_improvement_vs_benchmark": "avg_abs_error_improvement_vs_benchmark",
                "available_indicator_share": "avg_available_indicator_share",
            }
        )
        annual = annual.merge(surprise_annual, on=["state", "year"], how="left")
    return annual.sort_values(["state", "year"])


def policy_control_codebook() -> pd.DataFrame:
    """Document fields exported for downstream causal-policy projects."""
    rows = [
        ("avg_activity_index", "Average quarterly standardized regional activity index in the state-year."),
        ("avg_activity_momentum", "Average quarter-to-quarter change in the regional activity index."),
        ("avg_activity_percentile", "Within-state percentile rank of quarterly activity, averaged over the year."),
        ("avg_negative_indicator_breadth", "Average share of indicators deteriorating quarter over quarter."),
        ("avg_activity_surprise", "Average actual-minus-predicted nowcast surprise; positive means stronger than expected."),
        ("avg_abs_error_improvement_vs_benchmark", "Positive values mean the chosen model beat the benchmark in absolute error."),
        ("avg_available_indicator_share", "Average share of indicators available at the forecast origin."),
    ]
    return pd.DataFrame(rows, columns=["field", "definition"])
