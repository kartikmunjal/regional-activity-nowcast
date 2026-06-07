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

from .index import compare_indexes, dynamic_factor_index, standardized_composite
from .nowcast import ar1_forecast, bridge_nowcast, dfm_nowcast, quarterly_features, random_walk_forecast


def expanding_window_backtest(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    min_train_quarters: int = 12,
) -> pd.DataFrame:
    target = target.sort_values(["date", "state"]).copy()
    dates = sorted(target["date"].unique())
    rows = []
    feature_cols = [c for c in monthly_panel.columns if c not in {"date", "state"}]
    for test_date in dates[min_train_quarters:]:
        train_target = target[target["date"] < test_date]
        test_target = target[target["date"] == test_date]
        as_of = pd.Timestamp(test_date) + pd.Timedelta(days=45)
        q_features = quarterly_features(monthly_panel, as_of=as_of)
        train_x = train_target.merge(q_features, on=["date", "state"], how="left")
        test_x = test_target[["date", "state"]].merge(q_features, on=["date", "state"], how="left")
        usable_features = [c for c in feature_cols if c in train_x.columns]
        preds = {
            "random_walk": random_walk_forecast(train_target, test_target[["date", "state"]]),
            "ar1": ar1_forecast(train_target, test_target[["date", "state"]]),
            "bridge": bridge_nowcast(train_x[usable_features], train_target["real_gdp"], test_x[usable_features]),
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
                        "model": model,
                        "actual": actual_row["real_gdp"],
                        "prediction": float(pred),
                        "error": float(pred - actual_row["real_gdp"]),
                    }
                )
    return pd.DataFrame(rows)


def rmse_table(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.groupby("model")["error"]
        .apply(lambda x: float(np.sqrt(np.mean(np.square(x)))))
        .rename("rmse")
        .reset_index()
        .sort_values("rmse")
    )


def write_report_artifacts(monthly_panel: pd.DataFrame, target: pd.DataFrame, results: pd.DataFrame, report_dir: str | Path = "report") -> None:
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    composite = standardized_composite(monthly_panel)
    try:
        dfm = dynamic_factor_index(monthly_panel)
    except Exception:
        dfm = pd.DataFrame(columns=["date", "state", "dfm_index"])
    compare_indexes(composite, dfm, target).to_csv(path / "index_comparison.csv", index=False)
    rmse_table(results).to_csv(path / "oos_rmse_table.csv", index=False)

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

The nowcast target is quarterly BEA state real GDP. Monthly indicators are converted to quarterly means after applying release-lag assumptions, so each backtest date sees only data assumed to be available at the nowcast vintage. This is a simulated ragged edge unless ALFRED vintages are added for a given series. Benchmarks are random walk and state-specific AR(1); alternatives are a ridge bridge regression and a DFM-factor bridge.
"""
    (path / "methods.md").write_text(methods, encoding="utf-8")
