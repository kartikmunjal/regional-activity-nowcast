"""Economic research diagnostics built on top of the nowcast pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "2")

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from .data import target_for_model
from .nowcast import quarterly_features


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    return [c for c in frame.columns if c not in {"date", "state"}]


def lead_lag_study(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    max_lag_quarters: int = 4,
    target_transform: str = "qoq_ann",
) -> pd.DataFrame:
    """Estimate indicator/target correlations by state and lead length.

    `lag_quarters=1` means the indicator quarter is compared with next quarter's
    target, so positive correlations are leading relationships.
    """
    q_features = quarterly_features(monthly_panel)
    y = target_for_model(target, target_transform)[["date", "state", "target_value"]]
    rows = []
    for state, group in q_features.groupby("state"):
        state_y = y[y["state"] == state]
        for feature in _feature_columns(q_features):
            feature_series = group[["date", feature]].sort_values("date")
            for lag in range(max_lag_quarters + 1):
                shifted = feature_series.assign(date=feature_series["date"] + pd.offsets.QuarterEnd(lag))
                merged = shifted.merge(state_y, on="date", how="inner")
                corr = merged[feature].corr(merged["target_value"]) if len(merged.dropna()) >= 6 else np.nan
                rows.append(
                    {
                        "state": state,
                        "indicator": feature,
                        "lead_quarters": lag,
                        "correlation": float(corr) if pd.notna(corr) else np.nan,
                        "abs_correlation": float(abs(corr)) if pd.notna(corr) else np.nan,
                        "observations": int(len(merged.dropna())),
                    }
                )
    return pd.DataFrame(rows).sort_values(["abs_correlation"], ascending=False, na_position="last")


def bridge_sensitivity(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    target_transform: str = "qoq_ann",
) -> pd.DataFrame:
    """Fit state-specific standardized ridge bridges and report coefficients."""
    q_features = quarterly_features(monthly_panel)
    y = target_for_model(target, target_transform)[["date", "state", "target_value"]]
    features = _feature_columns(q_features)
    rows = []
    for state, x_state in q_features.groupby("state"):
        merged = x_state.merge(y[y["state"] == state], on=["date", "state"], how="inner").dropna(subset=["target_value"])
        if len(merged) < max(8, len(features) + 2):
            continue
        x = merged[features].fillna(merged[features].median(numeric_only=True).fillna(0))
        scaler = StandardScaler()
        model = Ridge(alpha=1.0).fit(scaler.fit_transform(x), merged["target_value"])
        for feature, coef in zip(features, model.coef_):
            rows.append(
                {
                    "state": state,
                    "indicator": feature,
                    "standardized_coefficient": float(coef),
                    "abs_coefficient": float(abs(coef)),
                    "target_transform": target_transform,
                }
            )
    return pd.DataFrame(rows).sort_values(["state", "abs_coefficient"], ascending=[True, False])


def state_sensitivity_clusters(sensitivity: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """Cluster states by bridge coefficient profiles."""
    if sensitivity.empty:
        return pd.DataFrame(columns=["state", "cluster", "dominant_indicator"])
    matrix = sensitivity.pivot_table(index="state", columns="indicator", values="standardized_coefficient", fill_value=0)
    k = min(n_clusters, len(matrix))
    labels = np.zeros(len(matrix), dtype=int) if k <= 1 else KMeans(n_clusters=k, random_state=7, n_init=20).fit_predict(matrix)
    dominant = matrix.abs().idxmax(axis=1)
    return pd.DataFrame({"state": matrix.index, "cluster": labels, "dominant_indicator": dominant.values})


def turning_point_flags(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    target_transform: str = "qoq_ann",
    slowdown_threshold: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate whether broad indicator deterioration anticipates weak target quarters."""
    q_features = quarterly_features(monthly_panel)
    features = _feature_columns(q_features)
    rows = []
    for state, group in q_features.groupby("state"):
        ordered = group.sort_values("date").copy()
        changes = ordered[features].diff()
        negative_breadth = (changes < 0).mean(axis=1)
        claims_spike = (
            ordered["claims"].pct_change().fillna(0) > ordered["claims"].pct_change().rolling(8, min_periods=4).std().fillna(np.inf)
            if "claims" in ordered
            else pd.Series(False, index=ordered.index)
        )
        rows.append(
            pd.DataFrame(
                {
                    "date": ordered["date"],
                    "state": state,
                    "negative_indicator_breadth": negative_breadth,
                    "claims_spike": claims_spike.astype(bool),
                    "slowdown_flag": (negative_breadth >= 0.6) | claims_spike.astype(bool),
                }
            )
        )
    flags = pd.concat(rows, ignore_index=True)
    y = target_for_model(target, target_transform)[["date", "state", "target_value"]]
    scored = flags.merge(y, on=["date", "state"], how="inner")
    scored["actual_slowdown"] = scored["target_value"] < slowdown_threshold
    summary_rows = []
    for state, group in scored.groupby("state"):
        tp = int((group["slowdown_flag"] & group["actual_slowdown"]).sum())
        fp = int((group["slowdown_flag"] & ~group["actual_slowdown"]).sum())
        fn = int((~group["slowdown_flag"] & group["actual_slowdown"]).sum())
        precision = tp / (tp + fp) if tp + fp else np.nan
        recall = tp / (tp + fn) if tp + fn else np.nan
        summary_rows.append({"state": state, "precision": precision, "recall": recall, "flags": int(group["slowdown_flag"].sum())})
    return scored, pd.DataFrame(summary_rows)


def spillover_study(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    indicator: str = "coincident",
    target_transform: str = "qoq_ann",
) -> pd.DataFrame:
    """Test whether one state's indicator leads another state's target."""
    q_features = quarterly_features(monthly_panel)
    y = target_for_model(target, target_transform)[["date", "state", "target_value"]]
    rows = []
    source = q_features[["date", "state", indicator]].dropna() if indicator in q_features else pd.DataFrame()
    if source.empty:
        return pd.DataFrame(columns=["source_state", "target_state", "indicator", "lead_quarters", "correlation", "observations"])
    for source_state, source_group in source.groupby("state"):
        shifted = source_group.assign(date=source_group["date"] + pd.offsets.QuarterEnd(1)).rename(
            columns={"state": "source_state", indicator: "source_indicator"}
        )
        for target_state, target_group in y.groupby("state"):
            merged = shifted.merge(target_group, on="date", how="inner")
            corr = merged["source_indicator"].corr(merged["target_value"]) if len(merged.dropna()) >= 6 else np.nan
            rows.append(
                {
                    "source_state": source_state,
                    "target_state": target_state,
                    "indicator": indicator,
                    "lead_quarters": 1,
                    "correlation": float(corr) if pd.notna(corr) else np.nan,
                    "observations": int(len(merged.dropna())),
                }
            )
    return pd.DataFrame(rows).sort_values("correlation", key=lambda s: s.abs(), ascending=False, na_position="last")


def bridge_contributions(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    target_transform: str = "qoq_ann",
) -> pd.DataFrame:
    """Decompose fitted bridge predictions into standardized feature contributions."""
    q_features = quarterly_features(monthly_panel)
    y = target_for_model(target, target_transform)[["date", "state", "target_value"]]
    features = _feature_columns(q_features)
    rows = []
    for state, x_state in q_features.groupby("state"):
        merged = x_state.merge(y[y["state"] == state], on=["date", "state"], how="inner").dropna(subset=["target_value"])
        if len(merged) < max(8, len(features) + 2):
            continue
        x = merged[features].fillna(merged[features].median(numeric_only=True).fillna(0))
        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x)
        model = Ridge(alpha=1.0).fit(x_scaled, merged["target_value"])
        contribution = x_scaled * model.coef_
        for row_idx, obs in merged.reset_index(drop=True).iterrows():
            for feature_idx, feature in enumerate(features):
                rows.append(
                    {
                        "date": obs["date"],
                        "state": state,
                        "indicator": feature,
                        "contribution": float(contribution[row_idx, feature_idx]),
                        "target_transform": target_transform,
                    }
                )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class FindingConfig:
    target_transform: str = "qoq_ann"
    max_lag_quarters: int = 4
    n_clusters: int = 4


def write_research_findings(
    monthly_panel: pd.DataFrame,
    target: pd.DataFrame,
    output_dir: str = "report",
    config: FindingConfig | None = None,
    data_label: str = "synthetic fixture",
) -> dict[str, pd.DataFrame]:
    """Generate research tables and a narrative markdown findings note."""
    cfg = config or FindingConfig()
    from pathlib import Path

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    lead_lag = lead_lag_study(monthly_panel, target, cfg.max_lag_quarters, cfg.target_transform)
    sensitivity = bridge_sensitivity(monthly_panel, target, cfg.target_transform)
    clusters = state_sensitivity_clusters(sensitivity, cfg.n_clusters)
    turning_points, turning_summary = turning_point_flags(monthly_panel, target, cfg.target_transform)
    spillovers = spillover_study(monthly_panel, target, target_transform=cfg.target_transform)
    contributions = bridge_contributions(monthly_panel, target, cfg.target_transform)

    outputs = {
        "lead_lag": lead_lag,
        "bridge_sensitivity": sensitivity,
        "state_clusters": clusters,
        "turning_points": turning_points,
        "turning_point_summary": turning_summary,
        "spillovers": spillovers,
        "bridge_contributions": contributions,
    }
    for name, frame in outputs.items():
        frame.to_csv(path / f"{name}.csv", index=False)

    top_contemporaneous = lead_lag.dropna().query("lead_quarters == 0").head(6)
    top_leads = lead_lag.dropna().query("lead_quarters > 0").head(8)
    top_sens = sensitivity.head(8)
    cluster_lines = clusters.sort_values(["cluster", "state"]).to_dict("records")
    narrative = ["# Phase 2: Research Findings", ""]
    narrative.append(f"Data label: **{data_label}**. Target transform: `{cfg.target_transform}`.")
    narrative.append("")
    narrative.append("These findings are generated mechanically from the loaded panel. Treat them as real empirical claims only after the registry is populated with verified live public series.")
    narrative.append("")
    narrative.append("## Contemporaneous Activity Signals")
    if top_contemporaneous.empty:
        narrative.append("No stable contemporaneous correlations were available.")
    else:
        for row in top_contemporaneous.to_dict("records"):
            direction = "moves with" if row["correlation"] >= 0 else "moves against"
            narrative.append(
                f"- {row['state']}: `{row['indicator']}` {direction} current-quarter growth "
                f"(correlation {row['correlation']:.3f}, {int(row['observations'])} observations)."
            )
    narrative.append("")
    narrative.append("## Leading Signals")
    if top_leads.empty:
        narrative.append("No stable leading correlations were available after requiring positive lead length.")
    else:
        for row in top_leads.to_dict("records"):
            direction = "positive" if row["correlation"] >= 0 else "negative"
            narrative.append(
                f"- {row['state']}: `{row['indicator']}` has a {direction} {int(row['lead_quarters'])}-quarter lead "
                f"signal for growth (correlation {row['correlation']:.3f}, {int(row['observations'])} observations)."
            )
    narrative.append("")
    narrative.append("## State Sensitivities")
    if top_sens.empty:
        narrative.append("No bridge sensitivity estimates were available.")
    else:
        for row in top_sens.to_dict("records"):
            sign = "positive" if row["standardized_coefficient"] >= 0 else "negative"
            narrative.append(
                f"- {row['state']}: `{row['indicator']}` has a {sign} standardized bridge coefficient "
                f"({row['standardized_coefficient']:.3f})."
            )
    narrative.append("")
    narrative.append("## Regional Clusters")
    if not cluster_lines:
        narrative.append("No state clusters were available.")
    else:
        for row in cluster_lines:
            narrative.append(f"- {row['state']}: cluster {int(row['cluster'])}, dominant indicator `{row['dominant_indicator']}`.")
    narrative.append("")
    narrative.append("## Turning-Point Screen")
    if turning_summary.empty:
        narrative.append("No turning-point evaluation was available.")
    else:
        for row in turning_summary.to_dict("records"):
            precision = "NA" if pd.isna(row["precision"]) else f"{row['precision']:.3f}"
            recall = "NA" if pd.isna(row["recall"]) else f"{row['recall']:.3f}"
            narrative.append(f"- {row['state']}: precision {precision}, recall {recall}, flags {int(row['flags'])}.")
    narrative.append("")
    narrative.append("## Interpretation Discipline")
    narrative.append(
        "The goal is to identify regional mechanisms, not just leaderboard scores. Strong findings should survive live data, "
        "alternative target transforms, and expanding-window evaluation."
    )
    (path / "research_findings.md").write_text("\n".join(narrative) + "\n", encoding="utf-8")
    return outputs
