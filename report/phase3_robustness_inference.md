# Phase 3: Robustness And Falsification

This phase adds checks that make the economic findings harder to dismiss as artifacts of one target definition, one forecast origin, or one unstable regression fit.

## Checks

- Target-transform robustness across GDP level, annualized quarter-over-quarter growth, and year-over-year growth.
- Forecast-origin robustness across alternative nowcast lags.
- Placebo lead-lag tests that shuffle targets within state.
- Expanding-window coefficient stability for bridge sensitivities.
- Economic sign audit against registry priors.

## Core Outputs

- `report/robustness_grid.csv`
- `report/lead_lag_placebo.csv`
- `report/coefficient_stability.csv`
- `report/coefficient_stability_summary.csv`
- `report/economic_sign_audit.csv`

## Interpretation Rule

A relationship should be presented as a serious research finding only if it is economically sensible, survives target-transform robustness, performs better than placebo, and remains reasonably stable over expanding windows.

