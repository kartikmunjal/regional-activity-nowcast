# Methods

This project builds a state-level activity index from public indicators and evaluates quarterly state real GDP nowcasts in a true expanding-window design.

The transparent baseline standardizes each indicator within state, reverses indicators where higher values mean weaker activity, and averages available z-scores. The model-based index uses `statsmodels` `DynamicFactorMQ` where enough observations are available, with a documented fallback for tiny smoke-test samples.

The nowcast target is quarterly BEA state real GDP, evaluated as a configurable level, annualized quarter-over-quarter growth, or year-over-year growth target. Monthly indicators are converted to quarterly means after applying release-lag assumptions, so each backtest date sees only data assumed to be available at the forecast origin. This is a simulated ragged edge unless ALFRED vintages are added for a given series.

Benchmarks include random walk, state-specific AR(1), state mean, pooled mean, peer average, and national-context bridge. Candidate models are a ridge bridge regression and a DFM-factor bridge. Tables include RMSE, MAE, bias, directional accuracy, and an approximate Diebold-Mariano comparison against AR(1). Data quality outputs report missingness, duplicate dates, outlier counts, and release-lag assumptions by state and series.
