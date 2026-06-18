# Phase 4: Live Empirical Pilot

This phase moves the project from a synthetic research scaffold toward actual empirical economics.

## Pilot Design

The initial live sample should use a deliberately diverse set of states rather than all 50 states immediately. The pilot states are listed in `config/pilot_states.yml` and cover technology/services, energy, housing, finance, manufacturing, logistics, tourism, and Sun Belt growth exposure.

## Workflow

1. Set `FRED_API_KEY` and `BEA_API_KEY`, or put them in a local `.env` file.
2. Run `scripts/discover_fred_series.py` to produce `report/fred_series_candidates.csv`.
3. Manually inspect candidate titles, units, frequency, seasonal adjustment, and date coverage.
4. Populate `config/series_registry.yml` only with confirmed IDs and set `verified: true` for those rows.
5. Run `scripts/run_live_pilot.py`.

The repo now includes `scripts/validate_api_keys.py` for provider checks and `scripts/bootstrap_fred_registry.py --verify` for standard FRED pilot-state mappings. A present but inactive BEA key or invalid Census key is recorded in `report/api_key_validation.csv` and blocks the full live pilot.

## Research Standard

Do not promote a finding into the README or abstract unless it uses verified public data, has adequate date coverage, survives robustness checks, and passes basic economic-sign review.
