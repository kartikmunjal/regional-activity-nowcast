# Phase 2: Research Findings

Data label: **verified public data pilot**. Target transform: `qoq_ann`.

These findings are generated mechanically from the loaded panel. Treat them as real empirical claims only after the registry is populated with verified live public series.

## Contemporaneous Activity Signals
- NJ: `coincident` moves with current-quarter growth (correlation 0.942, 39 observations).
- VT: `coincident` moves with current-quarter growth (correlation 0.930, 39 observations).
- NJ: `payroll` moves with current-quarter growth (correlation 0.927, 39 observations).
- IL: `coincident` moves with current-quarter growth (correlation 0.908, 39 observations).
- MI: `coincident` moves with current-quarter growth (correlation 0.907, 39 observations).
- IN: `coincident` moves with current-quarter growth (correlation 0.898, 39 observations).

## Leading Signals
- MS: `claims` has a positive 1-quarter lead signal for growth (correlation 0.690, 39 observations).
- AL: `claims` has a positive 1-quarter lead signal for growth (correlation 0.674, 39 observations).
- AL: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.643, 39 observations).
- WA: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.642, 39 observations).
- AR: `claims` has a positive 1-quarter lead signal for growth (correlation 0.631, 39 observations).
- AR: `coincident` has a negative 1-quarter lead signal for growth (correlation -0.622, 39 observations).
- FL: `claims` has a positive 1-quarter lead signal for growth (correlation 0.619, 39 observations).
- KY: `payroll` has a negative 1-quarter lead signal for growth (correlation -0.619, 39 observations).

## Placebo Screen
- AL: `claims` at 1 quarters has placebo p-value 0.048.
- AL: `payroll` at 1 quarters has placebo p-value 0.048.
- WA: `payroll` at 1 quarters has placebo p-value 0.048.
- AR: `claims` at 1 quarters has placebo p-value 0.048.
- AR: `coincident` at 1 quarters has placebo p-value 0.048.
- KY: `payroll` at 1 quarters has placebo p-value 0.048.

## State Sensitivities
- AL: `coincident` has a positive standardized bridge coefficient (6.184).
- AL: `payroll` has a positive standardized bridge coefficient (1.864).
- AL: `claims` has a positive standardized bridge coefficient (1.394).
- AL: `national_activity` has a positive standardized bridge coefficient (0.757).
- AR: `coincident` has a positive standardized bridge coefficient (2.391).
- AR: `payroll` has a positive standardized bridge coefficient (1.351).
- AR: `claims` has a negative standardized bridge coefficient (-0.230).
- AR: `national_activity` has a positive standardized bridge coefficient (0.136).

## Regional Clusters
- AZ: cluster 0, dominant indicator `coincident`.
- CA: cluster 0, dominant indicator `coincident`.
- FL: cluster 0, dominant indicator `coincident`.
- ID: cluster 0, dominant indicator `coincident`.
- IN: cluster 0, dominant indicator `coincident`.
- LA: cluster 0, dominant indicator `coincident`.
- MI: cluster 0, dominant indicator `coincident`.
- NH: cluster 0, dominant indicator `coincident`.
- OH: cluster 0, dominant indicator `coincident`.
- TN: cluster 0, dominant indicator `coincident`.
- VT: cluster 0, dominant indicator `coincident`.
- AR: cluster 1, dominant indicator `coincident`.
- DC: cluster 1, dominant indicator `payroll`.
- IA: cluster 1, dominant indicator `coincident`.
- KS: cluster 1, dominant indicator `payroll`.
- KY: cluster 1, dominant indicator `payroll`.
- ME: cluster 1, dominant indicator `coincident`.
- NV: cluster 1, dominant indicator `payroll`.
- NY: cluster 1, dominant indicator `payroll`.
- PA: cluster 1, dominant indicator `coincident`.
- RI: cluster 1, dominant indicator `payroll`.
- SD: cluster 1, dominant indicator `payroll`.
- UT: cluster 1, dominant indicator `coincident`.
- VA: cluster 1, dominant indicator `payroll`.
- MD: cluster 2, dominant indicator `payroll`.
- MT: cluster 2, dominant indicator `payroll`.
- ND: cluster 2, dominant indicator `payroll`.
- NM: cluster 2, dominant indicator `payroll`.
- WY: cluster 2, dominant indicator `payroll`.
- AL: cluster 3, dominant indicator `coincident`.
- CO: cluster 3, dominant indicator `coincident`.
- DE: cluster 3, dominant indicator `coincident`.
- GA: cluster 3, dominant indicator `coincident`.
- IL: cluster 3, dominant indicator `coincident`.
- MA: cluster 3, dominant indicator `coincident`.
- MN: cluster 3, dominant indicator `coincident`.
- MO: cluster 3, dominant indicator `coincident`.
- MS: cluster 3, dominant indicator `coincident`.
- NC: cluster 3, dominant indicator `coincident`.
- NE: cluster 3, dominant indicator `coincident`.
- NJ: cluster 3, dominant indicator `coincident`.
- OK: cluster 3, dominant indicator `coincident`.
- OR: cluster 3, dominant indicator `coincident`.
- SC: cluster 3, dominant indicator `coincident`.
- TX: cluster 3, dominant indicator `coincident`.
- WA: cluster 3, dominant indicator `coincident`.
- WI: cluster 3, dominant indicator `coincident`.
- WV: cluster 3, dominant indicator `coincident`.

## Coefficient Stability
- IN `national_activity`: mean coefficient 0.040, positive in 51.85% of expanding windows.
- TX `payroll`: mean coefficient 0.372, positive in 51.85% of expanding windows.
- FL `national_activity`: mean coefficient 0.023, positive in 48.15% of expanding windows.
- ID `payroll`: mean coefficient 0.196, positive in 44.44% of expanding windows.
- IA `claims`: mean coefficient 0.092, positive in 55.56% of expanding windows.
- ID `claims`: mean coefficient -0.110, positive in 44.44% of expanding windows.

## Turning-Point Screen
- AL: precision 0.250, recall 0.400, flags 8.
- AR: precision 0.286, recall 0.200, flags 7.
- AZ: precision 0.091, recall 0.250, flags 11.
- CA: precision 0.375, recall 0.500, flags 8.
- CO: precision 0.667, recall 0.667, flags 6.
- DC: precision 0.667, recall 0.143, flags 3.
- DE: precision 0.500, recall 0.385, flags 10.
- FL: precision 0.250, recall 0.667, flags 8.
- GA: precision 0.231, recall 0.600, flags 13.
- IA: precision 0.600, recall 0.353, flags 10.
- ID: precision 0.222, recall 0.286, flags 9.
- IL: precision 0.333, recall 0.200, flags 6.
- IN: precision 0.167, recall 0.167, flags 6.
- KS: precision 0.375, recall 0.333, flags 8.
- KY: precision 0.444, recall 0.400, flags 9.
- LA: precision 0.333, recall 0.154, flags 6.
- MA: precision 0.200, recall 0.222, flags 10.
- MD: precision 0.111, recall 0.143, flags 9.
- ME: precision 0.333, recall 0.286, flags 6.
- MI: precision 0.273, recall 0.273, flags 11.
- MN: precision 0.500, recall 0.357, flags 10.
- MO: precision 0.222, recall 0.250, flags 9.
- MS: precision 0.429, recall 0.214, flags 7.
- MT: precision 0.500, recall 0.455, flags 10.
- NC: precision 0.273, recall 0.500, flags 11.
- ND: precision 0.500, recall 0.235, flags 8.
- NE: precision 0.400, recall 0.308, flags 10.
- NH: precision 0.300, recall 0.231, flags 10.
- NJ: precision 0.250, recall 0.286, flags 8.
- NM: precision 0.500, recall 0.545, flags 12.
- NV: precision 0.375, recall 0.750, flags 8.
- NY: precision 0.286, recall 0.182, flags 7.
- OH: precision 0.333, recall 0.333, flags 9.
- OK: precision 0.444, recall 0.308, flags 9.
- OR: precision 0.250, recall 0.286, flags 8.
- PA: precision 0.125, recall 0.100, flags 8.
- RI: precision 0.429, recall 0.200, flags 7.
- SC: precision 0.200, recall 1.000, flags 10.
- SD: precision 0.750, recall 0.353, flags 8.
- TN: precision 0.167, recall 0.667, flags 12.
- TX: precision 0.111, recall 0.125, flags 9.
- UT: precision 0.100, recall 0.333, flags 10.
- VA: precision 0.286, recall 0.571, flags 14.
- VT: precision 0.250, recall 0.200, flags 8.
- WA: precision 0.250, recall 0.286, flags 8.
- WI: precision 0.500, recall 0.400, flags 8.
- WV: precision 0.750, recall 0.333, flags 8.
- WY: precision 0.455, recall 0.294, flags 11.

## Interpretation Discipline
The goal is to identify regional mechanisms, not just leaderboard scores. Strong findings should survive live data, alternative target transforms, and expanding-window evaluation.
