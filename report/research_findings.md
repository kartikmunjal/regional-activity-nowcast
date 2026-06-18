# Phase 2: Research Findings

Data label: **verified public data pilot**. Target transform: `qoq_ann`.

These findings are generated mechanically from the loaded panel. Treat them as real empirical claims only after the registry is populated with verified live public series.

## Contemporaneous Activity Signals
- IL: `coincident` moves with current-quarter growth (correlation 0.908, 39 observations).
- MI: `coincident` moves with current-quarter growth (correlation 0.907, 39 observations).
- OH: `coincident` moves with current-quarter growth (correlation 0.889, 39 observations).
- FL: `coincident` moves with current-quarter growth (correlation 0.866, 39 observations).
- NY: `payroll` moves with current-quarter growth (correlation 0.851, 39 observations).
- IL: `payroll` moves with current-quarter growth (correlation 0.851, 39 observations).

## Leading Signals
- FL: `claims` has a positive 1-quarter lead signal for growth (correlation 0.619, 39 observations).
- AZ: `claims` has a positive 1-quarter lead signal for growth (correlation 0.588, 39 observations).
- CA: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.585, 39 observations).
- MI: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.584, 39 observations).
- NC: `coincident` has a negative 1-quarter lead signal for growth (correlation -0.576, 39 observations).
- AZ: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.570, 39 observations).
- OH: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.569, 39 observations).
- NC: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.561, 39 observations).

## Placebo Screen
- NC: `coincident` at 1 quarters has placebo p-value 0.048.
- NC: `payroll` at 1 quarters has placebo p-value 0.048.
- PA: `payroll` at 1 quarters has placebo p-value 0.048.
- PA: `coincident` at 1 quarters has placebo p-value 0.048.
- IL: `payroll` at 1 quarters has placebo p-value 0.048.
- IL: `claims` at 1 quarters has placebo p-value 0.048.

## State Sensitivities
- AZ: `coincident` has a positive standardized bridge coefficient (8.273).
- AZ: `claims` has a positive standardized bridge coefficient (1.831).
- AZ: `payroll` has a negative standardized bridge coefficient (-1.672).
- AZ: `national_activity` has a positive standardized bridge coefficient (0.486).
- CA: `coincident` has a positive standardized bridge coefficient (10.088).
- CA: `payroll` has a negative standardized bridge coefficient (-3.423).
- CA: `national_activity` has a negative standardized bridge coefficient (-0.456).
- CA: `claims` has a positive standardized bridge coefficient (0.423).

## Regional Clusters
- AZ: cluster 0, dominant indicator `coincident`.
- CA: cluster 0, dominant indicator `coincident`.
- OH: cluster 0, dominant indicator `coincident`.
- NY: cluster 1, dominant indicator `payroll`.
- PA: cluster 1, dominant indicator `coincident`.
- IL: cluster 2, dominant indicator `coincident`.
- NC: cluster 2, dominant indicator `coincident`.
- TX: cluster 2, dominant indicator `coincident`.
- FL: cluster 3, dominant indicator `coincident`.
- MI: cluster 3, dominant indicator `coincident`.

## Coefficient Stability
- TX `payroll`: mean coefficient 0.372, positive in 51.85% of expanding windows.
- FL `national_activity`: mean coefficient 0.023, positive in 48.15% of expanding windows.
- NC `national_activity`: mean coefficient -0.032, positive in 55.56% of expanding windows.
- CA `national_activity`: mean coefficient -0.256, positive in 44.44% of expanding windows.
- OH `national_activity`: mean coefficient -0.073, positive in 44.44% of expanding windows.
- NY `national_activity`: mean coefficient -0.217, positive in 40.74% of expanding windows.

## Turning-Point Screen
- AZ: precision 0.091, recall 0.250, flags 11.
- CA: precision 0.375, recall 0.500, flags 8.
- FL: precision 0.250, recall 0.667, flags 8.
- IL: precision 0.333, recall 0.200, flags 6.
- MI: precision 0.273, recall 0.273, flags 11.
- NC: precision 0.273, recall 0.500, flags 11.
- NY: precision 0.286, recall 0.182, flags 7.
- OH: precision 0.333, recall 0.333, flags 9.
- PA: precision 0.125, recall 0.100, flags 8.
- TX: precision 0.111, recall 0.125, flags 9.

## Interpretation Discipline
The goal is to identify regional mechanisms, not just leaderboard scores. Strong findings should survive live data, alternative target transforms, and expanding-window evaluation.
