# Phase 1: Initial Nowcast Framework

This phase preserves the first implementation delivered from the original prompt: build a reproducible state-level activity index and nowcast quarterly state real GDP using public-data-shaped inputs, point-in-time release assumptions, and honest expanding-window evaluation.

## Scope

- State economic activity index:
  - transparent standardized z-score composite
  - `statsmodels` `DynamicFactorMQ` factor model
- Quarterly state real GDP nowcast:
  - ridge bridge regression
  - DFM-factor bridge
  - random walk, AR(1), state mean, pooled mean, peer average, and national-context benchmarks
- Real-time discipline:
  - forecast-origin metadata
  - registry release-lag assumptions
  - simulated ragged edge unless provider vintages are available
- Reporting:
  - OOS metrics
  - Diebold-Mariano tests vs AR(1)
  - data-quality checks
  - DFM diagnostics

## Status

The framework is structurally ready for verified public data. The default reproducible fixture remains synthetic until `config/series_registry.yml` is populated with provider-confirmed state series IDs and live API pulls are enabled.
