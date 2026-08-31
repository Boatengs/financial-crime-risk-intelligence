from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Profile the structural Elliptic2 feature store.")
    parser.add_argument("--input", default="data/derived/component_features.parquet")
    parser.add_argument("--output", default="results/component_feature_profile.json")
    args = parser.parse_args()

    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("duckdb is required: pip install -e .") from exc

    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"Feature store not found: {source}")

    con = duckdb.connect()
    src = source.as_posix()

    counts = con.execute(
        f"""
        SELECT
          count(*) AS rows,
          sum(CASE WHEN label = 1 THEN 1 ELSE 0 END) AS positive_rows,
          sum(CASE WHEN label = 0 THEN 1 ELSE 0 END) AS negative_rows,
          sum(CASE WHEN label IS NULL THEN 1 ELSE 0 END) AS null_labels
        FROM read_parquet('{src}')
        """
    ).fetchone()

    schema_rows = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{src}')").fetchall()
    columns = [row[0] for row in schema_rows]
    feature_columns = [c for c in columns if c not in {"component_id", "label"}]

    numeric_summary = con.execute(
        f"""
        SELECT
          label,
          count(*) AS components,
          avg(node_count) AS avg_node_count,
          approx_quantile(node_count, 0.5) AS median_node_count,
          max(node_count) AS max_node_count,
          avg(edge_count) AS avg_edge_count,
          approx_quantile(edge_count, 0.5) AS median_edge_count,
          max(edge_count) AS max_edge_count,
          avg(edges_per_node) AS avg_edges_per_node,
          avg(directed_density) AS avg_directed_density,
          avg(source_nodes) AS avg_source_nodes,
          avg(sink_nodes) AS avg_sink_nodes
        FROM read_parquet('{src}')
        GROUP BY label
        ORDER BY label
        """
    ).fetchall()

    null_expr = ", ".join(
        [f"sum(CASE WHEN \"{c}\" IS NULL THEN 1 ELSE 0 END) AS \"{c}\"" for c in feature_columns]
    )
    null_row = con.execute(f"SELECT {null_expr} FROM read_parquet('{src}')").fetchone()
    null_counts = {feature_columns[i]: int(null_row[i] or 0) for i in range(len(feature_columns))}

    profile = {
        "rows": int(counts[0]),
        "positive_rows": int(counts[1] or 0),
        "negative_rows": int(counts[2] or 0),
        "null_labels": int(counts[3] or 0),
        "feature_count": len(feature_columns),
        "feature_columns": feature_columns,
        "null_counts": null_counts,
        "summary_by_label": [
            {
                "label": int(row[0]),
                "components": int(row[1]),
                "avg_node_count": float(row[2]),
                "median_node_count": float(row[3]),
                "max_node_count": int(row[4]),
                "avg_edge_count": float(row[5]),
                "median_edge_count": float(row[6]),
                "max_edge_count": int(row[7]),
                "avg_edges_per_node": float(row[8]),
                "avg_directed_density": float(row[9]),
                "avg_source_nodes": float(row[10]),
                "avg_sink_nodes": float(row[11]),
            }
            for row in numeric_summary
        ],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
