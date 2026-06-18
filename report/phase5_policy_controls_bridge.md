# Phase 5: Policy-Controls Bridge

This phase turns the regional nowcast repo into a companion data product for causal-policy research.

## Research Purpose

The causal-policy project estimates minimum-wage effects using border-county designs. Those estimates can be biased or heterogeneous when states are at different points in the business cycle. This repo now exports state-quarter and state-year regional activity controls that can be merged into policy panels.

## Exported Objects

The policy-control export writes:

- `report/quarterly_policy_controls.csv`
- `report/nowcast_surprises.csv`
- `report/state_year_policy_controls.csv`
- `report/policy_control_codebook.csv`

The annual file is designed for downstream state-year policy panels. Key fields include:

- `avg_activity_index`: average regional activity index.
- `avg_activity_momentum`: average quarter-to-quarter change in activity.
- `avg_activity_percentile`: within-state activity rank.
- `avg_negative_indicator_breadth`: share of indicators deteriorating.
- `avg_activity_surprise`: actual-minus-predicted nowcast surprise.
- `avg_abs_error_improvement_vs_benchmark`: whether the selected nowcast beats a simple benchmark.
- `avg_available_indicator_share`: ragged-edge data availability.

## Economic Interpretation

These controls help separate policy effects from regional cycle conditions. For example, a minimum-wage increase occurring during a positive activity surprise is economically different from one occurring during a local slowdown, even if both occur in the same calendar year.

The controls can support:

- macro-cycle controls in border-county DiD regressions
- heterogeneity by pre-policy local activity
- sensitivity checks excluding recessionary or high-surprise state-years
- narrative discipline when estimated policy effects coincide with unusual local growth shocks

## Command

```bash
PYTHONPATH=src .venv/bin/python scripts/export_policy_controls.py \
  --target-transform qoq_ann \
  --model bridge \
  --benchmark ar1
```

The export uses existing processed monthly indicators, BEA state GDP targets, and `data/processed/backtest_results.csv` if available.
