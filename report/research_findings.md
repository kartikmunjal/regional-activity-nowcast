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

## Turning-Point Screen
- CA: precision 0.722, recall 0.591, flags 18.
- TX: precision 0.500, recall 0.474, flags 18.

## Interpretation Discipline
The goal is to identify regional mechanisms, not just leaderboard scores. Strong findings should survive live data, alternative target transforms, and expanding-window evaluation.
