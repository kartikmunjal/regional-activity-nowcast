"""Expanding-window out-of-sample evaluation and reporting."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib-cache").resolve()))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import (
    availability_matrix,
    data_quality_report,
    registry_release_lags,
    target_for_model,
)
from .index import compare_indexes, dynamic_factor_diagnostics, dynamic_factor_index, standardized_composite
from .nowcast import (
    ar1_forecast,
    bridge_nowcast,
    dfm_nowcast,
    national_context_bridge,
    peer_average_forecast,
    pooled_mean_forecast,
    quarterly_features,
    random_walk_forecast,
    state_mean_forecast,
)


def expanding_window_backtest(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    min_train_quarters: int = 12,
    target_transform: str = "level",
    nowcast_lag_days: int = 45,
    release_lags: dict[str, int] | None = None,
) -> pd.DataFrame:
    target = target_for_model(target, transform=target_transform).sort_values(["date", "state"]).copy()
    dates = sorted(target["date"].unique())
    rows = []
    feature_cols = [c for c in monthly_panel.columns if c not in {"date", "state"}]
    for test_date in dates[min_train_quarters:]:
        train_target = target[target["date"] < test_date]
        test_target = target[target["date"] == test_date]
        as_of = pd.Timestamp(test_date) + pd.Timedelta(days=nowcast_lag_days)
        q_features = quarterly_features(monthly_panel, as_of=as_of, release_lags=release_lags)
        train_x = train_target.merge(q_features, on=["date", "state"], how="left")
        test_x = test_target[["date", "state"]].merge(q_features, on=["date", "state"], how="left")
        usable_features = [c for c in feature_cols if c in train_x.columns]
        availability = availability_matrix(monthly_panel[monthly_panel["date"] <= test_date], as_of, release_lags)
        avail_cols = [c for c in availability.columns if c not in {"date", "state"}]
        available_share = float(availability[avail_cols].to_numpy().mean()) if avail_cols else np.nan
        preds = {
            "random_walk": random_walk_forecast(train_target, test_target[["date", "state"]]),
            "ar1": ar1_forecast(train_target, test_target[["date", "state"]]),
            "state_mean": state_mean_forecast(train_target, test_target[["date", "state"]]),
            "pooled_mean": pooled_mean_forecast(train_target, test_target[["date", "state"]]),
            "peer_average": peer_average_forecast(train_target, test_target[["date", "state"]]),
            "national_bridge": national_context_bridge(train_x[usable_features], train_target["target_value"], test_x[usable_features]),
            "bridge": bridge_nowcast(train_x[usable_features], train_target["target_value"], test_x[usable_features]),
            "dfm": dfm_nowcast(
                monthly_panel[monthly_panel["date"] < test_date],
                train_target,
                monthly_panel[monthly_panel["date"] <= as_of],
                test_target[["date", "state"]],
            ),
        }
        for model, values in preds.items():
            for (_, actual_row), pred in zip(test_target.iterrows(), values):
                rows.append(
                    {
                        "date": test_date,
                        "state": actual_row["state"],
                        "forecast_origin": as_of,
                        "target_transform": target_transform,
                        "nowcast_lag_days": nowcast_lag_days,
                        "available_indicator_share": available_share,
                        "model": model,
                        "actual": actual_row["target_value"],
                        "prediction": float(pred),
                        "error": float(pred - actual_row["target_value"]),
                    }
                )
    return pd.DataFrame(rows)


def rmse_table(results: pd.DataFrame) -> pd.DataFrame:
    return metric_table(results)[["model", "rmse", "mae", "bias", "directional_accuracy", "n"]].sort_values("rmse")


def metric_table(results: pd.DataFrame) -> pd.DataFrame:
    def direction(group: pd.DataFrame) -> float:
        actual_delta = group.sort_values("date").groupby("state")["actual"].diff()
        pred_delta = group.sort_values("date").groupby("state")["prediction"].diff()
        ok = actual_delta.notna() & pred_delta.notna()
        if not ok.any():
            return np.nan
        return float((np.sign(actual_delta[ok]) == np.sign(pred_delta[ok])).mean())

    rows = []
    for model, group in results.groupby("model"):
        rows.append(
            {
                "model": model,
                "rmse": float(np.sqrt(np.mean(np.square(group["error"])))),
                "mae": float(np.mean(np.abs(group["error"]))),
                "bias": float(group["error"].mean()),
                "directional_accuracy": direction(group),
                "n": int(len(group)),
            }
        )
    return pd.DataFrame(rows).sort_values("rmse")


def diebold_mariano_table(results: pd.DataFrame, benchmark: str = "ar1") -> pd.DataFrame:
    """Approximate DM test using squared-error loss and a normal reference."""
    try:
        from scipy import stats
    except ImportError:
        return pd.DataFrame()

    base = results[results["model"] == benchmark][["date", "state", "error"]].rename(columns={"error": "benchmark_error"})
    rows = []
    for model, group in results.groupby("model"):
        if model == benchmark:
            continue
        merged = group.merge(base, on=["date", "state"], how="inner")
        if len(merged) < 3:
            continue
        diff = np.square(merged["error"]) - np.square(merged["benchmark_error"])
        stat = float(diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff)))) if diff.std(ddof=1) else np.nan
        p_value = float(2 * (1 - stats.norm.cdf(abs(stat)))) if np.isfinite(stat) else np.nan
        rows.append({"model": model, "benchmark": benchmark, "dm_stat": stat, "p_value": p_value, "n": int(len(diff))})
    return pd.DataFrame(rows).sort_values("p_value", na_position="last")


def write_report_artifacts(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    results: pd.DataFrame,
    report_dir: str | Path = "report",
    registry: dict | None = None,
) -> None:
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    release_lags = registry_release_lags(registry) if registry else {}
    composite = standardized_composite(monthly_panel)
    try:
        dfm = dynamic_factor_index(monthly_panel)
    except Exception:
        dfm = pd.DataFrame(columns=["date", "state", "dfm_index"])
    compare_indexes(composite, dfm, target).to_csv(path / "index_comparison.csv", index=False)
    dynamic_factor_diagnostics(monthly_panel).to_csv(path / "dfm_diagnostics.csv", index=False)
    metric_table(results).to_csv(path / "oos_metrics_table.csv", index=False)
    rmse_table(results).to_csv(path / "oos_rmse_table.csv", index=False)
    diebold_mariano_table(results).to_csv(path / "diebold_mariano_vs_ar1.csv", index=False)
    data_quality_report(monthly_panel, target, release_lags).to_csv(path / "data_quality_report.csv", index=False)

    first_state = sorted(monthly_panel["state"].unique())[0]
    fig, ax = plt.subplots(figsize=(9, 4))
    comp_state = composite[composite["state"] == first_state]
    ax.plot(comp_state["date"], comp_state["composite_index"], label="Composite")
    if not dfm.empty:
        dfm_state = dfm[dfm["state"] == first_state]
        ax.plot(dfm_state["date"], dfm_state["dfm_index"], label="DFM")
    ax.set_title(f"{first_state}: activity index comparison")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path / "index-vs-official-series.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    for model, group in results.groupby("model"):
        error_by_date = group.groupby("date")["error"].mean()
        ax.plot(error_by_date.index, error_by_date.values, label=model)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Nowcast error over time")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path / "nowcast-error-over-time.png", dpi=160)
    plt.close(fig)

    methods = """# Methods

This project builds a state-level activity index from public indicators and evaluates quarterly state real GDP nowcasts in a true expanding-window design.

The transparent baseline standardizes each indicator within state, reverses indicators where higher values mean weaker activity, and averages available z-scores. The model-based index uses `statsmodels` `DynamicFactorMQ` where enough observations are available, with a documented fallback for tiny smoke-test samples.

The nowcast target is quarterly BEA state real GDP, evaluated as a configurable level, annualized quarter-over-quarter growth, or year-over-year growth target. Monthly indicators are converted to quarterly means after applying release-lag assumptions, so each backtest date sees only data assumed to be available at the forecast origin. This is a simulated ragged edge unless ALFRED vintages are added for a given series.

Benchmarks include random walk, state-specific AR(1), state mean, pooled mean, peer average, and national-context bridge. Candidate models are a ridge bridge regression and a DFM-factor bridge. Tables include RMSE, MAE, bias, directional accuracy, and an approximate Diebold-Mariano comparison against AR(1). Data quality outputs report missingness, duplicate dates, outlier counts, and release-lag assumptions by state and series.
"""
    (path / "methods.md").write_text(methods, encoding="utf-8")
