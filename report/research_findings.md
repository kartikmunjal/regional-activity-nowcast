# Phase 2: Research Findings

Data label: **synthetic CA/TX fixture**. Target transform: `qoq_ann`.

These findings are generated mechanically from the loaded panel. Treat them as real empirical claims only after the registry is populated with verified live public series.

## Contemporaneous Activity Signals
- TX: `payroll` moves with current-quarter growth (correlation 0.685, 39 observations).
- CA: `payroll` moves with current-quarter growth (correlation 0.637, 39 observations).
- CA: `coincident` moves with current-quarter growth (correlation 0.590, 39 observations).
- TX: `claims` moves against current-quarter growth (correlation -0.576, 39 observations).
- TX: `coincident` moves with current-quarter growth (correlation 0.543, 39 observations).
- CA: `claims` moves against current-quarter growth (correlation -0.459, 39 observations).

## Leading Signals
- CA: `business_formations` has a negative 3-quarter lead signal for growth (correlation -0.434, 37 observations).
- CA: `permits` has a negative 3-quarter lead signal for growth (correlation -0.408, 37 observations).
- CA: `business_formations` has a negative 4-quarter lead signal for growth (correlation -0.373, 36 observations).
- CA: `permits` has a negative 4-quarter lead signal for growth (correlation -0.373, 36 observations).
- CA: `business_formations` has a negative 2-quarter lead signal for growth (correlation -0.369, 38 observations).
- CA: `business_formations` has a negative 1-quarter lead signal for growth (correlation -0.352, 39 observations).
- CA: `payroll` has a positive 1-quarter lead signal for growth (correlation 0.294, 39 observations).
- CA: `coincident` has a positive 1-quarter lead signal for growth (correlation 0.290, 39 observations).

## Placebo Screen
- CA: `business_formations` at 3 quarters has placebo p-value 0.030.
- CA: `permits` at 4 quarters has placebo p-value 0.030.
- CA: `permits` at 3 quarters has placebo p-value 0.040.
- CA: `business_formations` at 4 quarters has placebo p-value 0.040.
- CA: `business_formations` at 1 quarters has placebo p-value 0.040.
- CA: `business_formations` at 2 quarters has placebo p-value 0.050.

## State Sensitivities
- CA: `payroll` has a positive standardized bridge coefficient (0.434).
- CA: `coincident` has a positive standardized bridge coefficient (0.266).
- CA: `permits` has a negative standardized bridge coefficient (-0.207).
- CA: `business_formations` has a positive standardized bridge coefficient (0.166).
- CA: `claims` has a positive standardized bridge coefficient (0.137).
- CA: `national_activity` has a positive standardized bridge coefficient (0.057).
- TX: `payroll` has a positive standardized bridge coefficient (0.478).
- TX: `claims` has a negative standardized bridge coefficient (-0.220).

## Regional Clusters
- CA: cluster 0, dominant indicator `payroll`.
- TX: cluster 1, dominant indicator `payroll`.

## Coefficient Stability
- TX `coincident`: mean coefficient 0.053, positive in 62.96% of expanding windows.
- TX `permits`: mean coefficient -0.047, positive in 29.63% of expanding windows.
- TX `claims`: mean coefficient -0.087, positive in 29.63% of expanding windows.
- CA `permits`: mean coefficient -0.236, positive in 14.81% of expanding windows.
- CA `business_formations`: mean coefficient 0.227, positive in 92.59% of expanding windows.
- CA `claims`: mean coefficient 0.161, positive in 96.30% of expanding windows.

## Turning-Point Screen
- CA: precision 0.722, recall 0.591, flags 18.
- TX: precision 0.500, recall 0.474, flags 18.

## Interpretation Discipline
The goal is to identify regional mechanisms, not just leaderboard scores. Strong findings should survive live data, alternative target transforms, and expanding-window evaluation.
