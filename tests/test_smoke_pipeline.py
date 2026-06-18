from pathlib import Path

from regional_activity_nowcast.data import apply_indicator_transforms, make_synthetic_panel, registry_series, target_for_model
from regional_activity_nowcast.evaluate import expanding_window_backtest, metric_table, rmse_table, write_report_artifacts
from regional_activity_nowcast.index import dynamic_factor_index, standardized_composite
from regional_activity_nowcast.policy_controls import (
    annual_policy_controls,
    nowcast_surprises,
    policy_control_codebook,
    quarterly_activity_controls,
)
from regional_activity_nowcast.research import FindingConfig, robustness_grid, write_research_findings


def test_full_pipeline_smoke(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monthly, target = make_synthetic_panel(["CA"], "2018-01-01", "2023-12-31")
    registry = {
        "indicators": [
            {"name": "payroll", "transform": "pct_change"},
            {"name": "claims", "transform": "pct_change"},
            {"name": "permits", "transform": "level"},
        ]
    }
    transformed = apply_indicator_transforms(monthly, registry)
    assert transformed["payroll"].isna().sum() == 1
    registry_with_ids = {
        "indicators": [
            {
                "name": "payroll",
                "source": "FRED",
                "frequency": "monthly",
                "release_lag_days": 21,
                "transform": "pct_change",
                "expected_sign": "positive",
                "verified": True,
                "series_by_state": {"CA": "DUMMY"},
            }
        ]
    }
    series_rows = registry_series(registry_with_ids, states=["CA"], source="FRED")
    assert series_rows[0].name == "payroll"
    composite = standardized_composite(monthly)
    assert {"date", "state", "composite_index"}.issubset(composite.columns)
    dfm = dynamic_factor_index(monthly)
    assert set(dfm.columns) == {"date", "state", "dfm_index"}

    results = expanding_window_backtest(monthly, target, min_train_quarters=8)
    table = rmse_table(results)
    assert set(results["model"]) == {
        "random_walk",
        "ar1",
        "state_mean",
        "pooled_mean",
        "peer_average",
        "national_bridge",
        "bridge",
        "dfm",
    }
    assert {"forecast_origin", "target_transform", "available_indicator_share"}.issubset(results.columns)
    assert table["rmse"].notna().all()
    assert metric_table(results)["mae"].notna().all()
    assert "target_value" in target_for_model(target, "qoq_ann").columns

    write_report_artifacts(monthly, target, results, report_dir="report")
    assert Path("report/oos_rmse_table.csv").exists()
    assert Path("report/oos_metrics_table.csv").exists()
    assert Path("report/data_quality_report.csv").exists()
    assert Path("report/dfm_diagnostics.csv").exists()
    assert Path("report/methods.md").exists()

    findings = write_research_findings(
        monthly,
        target,
        output_dir="report",
        config=FindingConfig(target_transform="qoq_ann", max_lag_quarters=2, placebo_permutations=3),
        registry=registry,
    )
    assert not findings["lead_lag"].empty
    assert "lead_lag_placebo" in findings
    grid = robustness_grid(monthly, target, target_transforms=["level"], nowcast_lags=[45], min_train_quarters=8)
    assert not grid.empty
    assert Path("report/research_findings.md").exists()


def test_policy_controls_export_smoke(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monthly, target = make_synthetic_panel(["CA", "TX"], "2016-01-01", "2023-12-31")
    results = expanding_window_backtest(monthly, target, min_train_quarters=8, target_transform="qoq_ann")
    q_controls = quarterly_activity_controls(monthly, target, target_transform="qoq_ann")
    surprises = nowcast_surprises(results, model="bridge", benchmark="ar1")
    annual = annual_policy_controls(q_controls, surprises)
    codebook = policy_control_codebook()
    assert {"composite_index", "activity_momentum", "negative_indicator_breadth"}.issubset(q_controls.columns)
    assert {"activity_surprise", "abs_error_improvement_vs_benchmark"}.issubset(surprises.columns)
    assert {"state", "year", "avg_activity_index", "avg_activity_surprise"}.issubset(annual.columns)
    assert set(annual["state"]) == {"CA", "TX"}
    assert not codebook.empty
