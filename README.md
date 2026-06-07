# regional-activity-nowcast

State-level US economic activity indexes and real-time-style nowcasts of quarterly BEA state real GDP from free public data.

## Thesis

Regional activity can be summarized with a small common factor extracted from payrolls, claims, coincident indexes, permits, business formation, and national context data. The repo compares a transparent standardized-z-score composite against a `statsmodels` `DynamicFactorMQ` estimator, then tests whether monthly indicators improve state real GDP nowcasts versus random-walk and AR(1) benchmarks.

## Data Sources And Provenance

- FRED and ALFRED: state claims, state nonfarm payrolls, Philadelphia Fed state coincident indexes, and national context series. Get a key at https://fred.stlouisfed.org/docs/api/api_key.html and set `FRED_API_KEY`.
- Census API: Building Permits Survey, Business Formation Statistics, and ACS demographics. Get a key at https://api.census.gov/data/key_signup.html and set `CENSUS_API_KEY`.
- BEA API: quarterly state real GDP target. Get a key at https://apps.bea.gov/API/signup/ and set `BEA_API_KEY`.
- BLS API: QCEW, CES, and LAUS validation data. Set `BLS_API_KEY` if using registered BLS calls.

Raw pulls are cached under `data/raw/` with the fetch date and sidecar JSON provenance. Series IDs must be verified through provider metadata before live use; the current smoke-test path uses deterministic synthetic fixture data so tests do not depend on API keys. The audit surface for live work is `config/series_registry.yml`, which records source, frequency, transform, expected sign, release lag, vintage policy, and verification status.

## Methods

The composite index standardizes each indicator within state and averages available z-scores, with unemployment claims inverted. The DFM path uses `statsmodels.tsa.statespace.dynamic_factor_mq.DynamicFactorMQ` to estimate a one-factor state activity signal.

The nowcast target is quarterly BEA state real GDP, evaluated as `level`, annualized quarter-over-quarter growth (`qoq_ann`), or year-over-year growth (`yoy`). Monthly data are converted to quarterly means after applying the registry release-lag table. The expanding-window backtest refits models using only prior target observations and only indicators assumed released as of the forecast origin.

Benchmarks now include random walk, state-specific AR(1), state mean, pooled mean, peer average, and national-context bridge. Candidate models are ridge bridge regression and DFM-factor bridge. Reports include RMSE, MAE, bias, directional accuracy, Diebold-Mariano tests versus AR(1), data-quality diagnostics, index comparison, and error-over-time charts.

## What Is Real Vs Simulated

Real: package structure, provider interfaces, caching discipline, series registry, series verification helpers, DFM/composite estimators, expanding-window evaluation, benchmark comparisons, target transforms, diagnostics, report generation, and API-key documentation.

Simulated: the default smoke pipeline uses synthetic indicator and GDP data. Ragged-edge availability is simulated with release-lag assumptions unless ALFRED vintages are wired for a specific FRED series.

## Point-In-Time Assumptions

Default release lags are 7 days for weekly FRED series, 21 days for monthly FRED/BLS series, 30 days for Census monthly series, and 90 days for BEA quarterly GDP. These assumptions live in `config/series_registry.yml` and should be audited against each production series calendar before publishing live metrics. Backtest rows include `forecast_origin`, `nowcast_lag_days`, and `available_indicator_share`.

## Latest Metrics

Current synthetic fixture run, CA and TX, 2015-01-01 through 2024-12-31, expanding-window backtest with 12 initial training quarters, target transform `level`:

| Model | OOS RMSE |
| --- | ---: |
| bridge | 1.065583 |
| random_walk | 1.163414 |
| ar1 | 1.241417 |
| state_mean | 3.968898 |
| national_bridge | 8.268097 |
| dfm | 9.767166 |
| pooled_mean | 9.796142 |
| peer_average | 19.303375 |

These are smoke-test metrics, not live economic claims. Regenerate `report/oos_rmse_table.csv` after switching to verified live public data.

## Reproduce Latest Result

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python scripts/fetch_data.py --synthetic --states CA TX --start 2015-01-01 --end 2024-12-31
PYTHONPATH=src .venv/bin/python scripts/build_index.py
PYTHONPATH=src .venv/bin/python scripts/backtest.py --min-train-quarters 12 --target-transform level --nowcast-lag-days 45
PYTHONPATH=src .venv/bin/python scripts/run_research_findings.py --target-transform qoq_ann --max-lag-quarters 4 --clusters 4 --data-label "synthetic CA/TX fixture"
PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Phased Research Workflow

Phase 1 is the initial deliverable from the original prompt: public-data-shaped data access, state activity indexes, DFM and bridge nowcasts, random-walk/AR(1) benchmarks, expanding-window evaluation, simulated ragged-edge discipline, report artifacts, tests, README, requirements, and MIT license. It is preserved in `report/phase1_initial_framework.md`.

Phase 2 and later are research extensions added after the initial framework: verified-registry discipline, vintage-ready FRED helpers, lead-lag analysis, state sensitivity profiles, regional clusters, turning-point screens, spillover checks, and bridge contribution tables. Phase 2 is described in `report/phase2_research_layer.md` and generated into `report/research_findings.md`.

Key generated files:

- `report/oos_metrics_table.csv`
- `report/oos_rmse_table.csv`
- `report/diebold_mariano_vs_ar1.csv`
- `report/data_quality_report.csv`
- `report/dfm_diagnostics.csv`
- `report/index_comparison.csv`
- `report/index-vs-official-series.png`
- `report/nowcast-error-over-time.png`
- `report/research_findings.md`
- `report/lead_lag.csv`
- `report/bridge_sensitivity.csv`
- `report/state_clusters.csv`
- `report/turning_point_summary.csv`
- `report/spillovers.csv`
- `report/bridge_contributions.csv`

## Live Registry Verification

Populate `config/series_registry.yml` with provider-confirmed IDs, mark rows `verified: true` only after checking source metadata, then run:

```bash
FRED_API_KEY=... PYTHONPATH=src .venv/bin/python scripts/verify_registry.py --states CA
```

The verifier writes `report/registry_verification.csv`. FRED-hosted series can also be fetched as-of a vintage date through the `fetch_fred_series_as_of` helper; production work should use that path where ALFRED vintages are available.

## Limitations

This is a correct, reproducible framework rather than a tuned showcase. Live indicator mappings still need state-by-state verified `SeriesSpec` entries, and production real-time work should prefer ALFRED vintages wherever available. If the DFM only ties or barely beats AR(1), the reports should say that plainly.
