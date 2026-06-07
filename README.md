# regional-activity-nowcast

State-level US economic activity indexes and real-time-style nowcasts of quarterly BEA state real GDP from free public data.

## Thesis

Regional activity can be summarized with a small common factor extracted from payrolls, claims, coincident indexes, permits, business formation, and national context data. The repo compares a transparent standardized-z-score composite against a `statsmodels` `DynamicFactorMQ` estimator, then tests whether monthly indicators improve state real GDP nowcasts versus random-walk and AR(1) benchmarks.

## Data Sources And Provenance

- FRED and ALFRED: state claims, state nonfarm payrolls, Philadelphia Fed state coincident indexes, and national context series. Get a key at https://fred.stlouisfed.org/docs/api/api_key.html and set `FRED_API_KEY`.
- Census API: Building Permits Survey, Business Formation Statistics, and ACS demographics. Get a key at https://api.census.gov/data/key_signup.html and set `CENSUS_API_KEY`.
- BEA API: quarterly state real GDP target. Get a key at https://apps.bea.gov/API/signup/ and set `BEA_API_KEY`.
- BLS API: QCEW, CES, and LAUS validation data. Set `BLS_API_KEY` if using registered BLS calls.

Raw pulls are cached under `data/raw/` with the fetch date and sidecar JSON provenance. Series IDs must be verified through provider metadata before live use; the current smoke-test path uses deterministic synthetic fixture data so tests do not depend on API keys.

## Methods

The composite index standardizes each indicator within state and averages available z-scores, with unemployment claims inverted. The DFM path uses `statsmodels.tsa.statespace.dynamic_factor_mq.DynamicFactorMQ` to estimate a one-factor state activity signal.

The nowcast target is quarterly BEA state real GDP. Monthly data are converted to quarterly means after applying a documented release-lag table. The expanding-window backtest refits models using only prior target observations and only indicators assumed released as of the nowcast date.

## What Is Real Vs Simulated

Real: package structure, provider interfaces, caching discipline, series verification helpers, DFM/composite estimators, expanding-window evaluation, benchmark comparisons, report generation, and API-key documentation.

Simulated: the default smoke pipeline uses synthetic indicator and GDP data. Ragged-edge availability is simulated with release-lag assumptions unless ALFRED vintages are wired for a specific FRED series.

## Point-In-Time Assumptions

Default release lags are 7 days for weekly FRED series, 21 days for monthly FRED/BLS series, 30 days for Census monthly series, and 90 days for BEA quarterly GDP. These assumptions are conservative placeholders and should be audited against each production series calendar before publishing live metrics.

## Latest Metrics

Current synthetic fixture run, CA, 2015-01-01 through 2024-12-31, expanding-window backtest with 12 initial training quarters:

| Model | OOS RMSE |
| --- | ---: |
| bridge | 0.555422 |
| dfm | 0.673860 |
| random_walk | 1.106456 |
| ar1 | 1.183801 |

These are smoke-test metrics, not live economic claims. Regenerate `report/oos_rmse_table.csv` after switching to verified live public data.

## Reproduce Latest Result

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python scripts/fetch_data.py --synthetic --states CA --start 2015-01-01 --end 2024-12-31
PYTHONPATH=src .venv/bin/python scripts/build_index.py
PYTHONPATH=src .venv/bin/python scripts/backtest.py --min-train-quarters 12
PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Limitations

This is a correct, reproducible framework rather than a tuned showcase. Live indicator mappings still need state-by-state verified `SeriesSpec` entries, and production real-time work should prefer ALFRED vintages wherever available. If the DFM only ties or barely beats AR(1), the reports should say that plainly.
