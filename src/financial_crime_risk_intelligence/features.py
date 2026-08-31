from __future__ import annotations

import pandas as pd


def component_structural_features(nodes: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    """Build simple explainable structural features for canonical fixture/component tables.

    Expected columns:
      nodes: component_id, node_id
      edges: component_id, source, target
    """
    node_counts = nodes.groupby("component_id")["node_id"].nunique().rename("node_count")
    edge_counts = edges.groupby("component_id").size().rename("edge_count")

    degree_rows = []
    for component_id, group in edges.groupby("component_id"):
        indeg = group.groupby("target").size()
        outdeg = group.groupby("source").size()
        all_nodes = set(indeg.index).union(outdeg.index)
        totals = [int(indeg.get(n, 0) + outdeg.get(n, 0)) for n in all_nodes]
        degree_rows.append(
            {
                "component_id": component_id,
                "mean_in_degree": float(indeg.mean()) if len(indeg) else 0.0,
                "mean_out_degree": float(outdeg.mean()) if len(outdeg) else 0.0,
                "max_degree": max(totals) if totals else 0,
            }
        )
    degree = pd.DataFrame(degree_rows).set_index("component_id") if degree_rows else pd.DataFrame()

    result = pd.concat([node_counts, edge_counts], axis=1).fillna(0).reset_index()
    if not degree.empty:
        result = result.merge(degree.reset_index(), on="component_id", how="left")
    else:
        result["mean_in_degree"] = 0.0
        result["mean_out_degree"] = 0.0
        result["max_degree"] = 0.0

    n = result["node_count"].clip(lower=1)
    result["density"] = result["edge_count"] / (n * (n - 1)).replace(0, 1)
    return result.fillna(0)
