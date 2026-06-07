# Methods

This project builds a state-level activity index from public indicators and evaluates quarterly state real GDP nowcasts in a true expanding-window design.

The transparent baseline standardizes each indicator within state, reverses indicators where higher values mean weaker activity, and averages available z-scores. The model-based index uses `statsmodels` `DynamicFactorMQ` where enough observations are available, with a documented fallback for tiny smoke-test samples.

The nowcast target is quarterly BEA state real GDP. Monthly indicators are converted to quarterly means after applying release-lag assumptions, so each backtest date sees only data assumed to be available at the nowcast vintage. This is a simulated ragged edge unless ALFRED vintages are added for a given series. Benchmarks are random walk and state-specific AR(1); alternatives are a ridge bridge regression and a DFM-factor bridge.
