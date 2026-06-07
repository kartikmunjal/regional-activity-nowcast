from pathlib import Path

from regional_activity_nowcast.data import make_synthetic_panel
from regional_activity_nowcast.evaluate import expanding_window_backtest, rmse_table, write_report_artifacts
from regional_activity_nowcast.index import dynamic_factor_index, standardized_composite


def test_full_pipeline_smoke(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monthly, target = make_synthetic_panel(["CA"], "2018-01-01", "2023-12-31")
    composite = standardized_composite(monthly)
    assert {"date", "state", "composite_index"}.issubset(composite.columns)
    dfm = dynamic_factor_index(monthly)
    assert set(dfm.columns) == {"date", "state", "dfm_index"}

    results = expanding_window_backtest(monthly, target, min_train_quarters=8)
    table = rmse_table(results)
    assert set(results["model"]) == {"random_walk", "ar1", "bridge", "dfm"}
    assert table["rmse"].notna().all()

    write_report_artifacts(monthly, target, results, report_dir="report")
    assert Path("report/oos_rmse_table.csv").exists()
    assert Path("report/methods.md").exists()

