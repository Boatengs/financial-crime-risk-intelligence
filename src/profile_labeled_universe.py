from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Profile the labeled Elliptic2 universe.")
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output", default="results/elliptic2_labeled_profile.json")
    args = parser.parse_args()

    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("duckdb is required: pip install -e .") from exc

    raw = Path(args.raw_dir)
    cc = (raw / "connected_components.csv").as_posix()
    nodes = (raw / "nodes.csv").as_posix()
    edges = (raw / "edges.csv").as_posix()

    missing = [p for p in [raw / "connected_components.csv", raw / "nodes.csv", raw / "edges.csv"] if not p.exists()]
    if missing:
        raise SystemExit(f"Missing files: {[p.name for p in missing]}")

    con = duckdb.connect()

    label_rows = con.execute(
        f"""
        SELECT lower(trim(CAST(ccLabel AS VARCHAR))) AS label, count(*) AS components
        FROM read_csv_auto('{cc}')
        GROUP BY 1 ORDER BY components DESC
        """
    ).fetchall()

    node_summary = con.execute(
        f"""
        WITH n AS (
          SELECT ccId, count(*) AS node_count
          FROM read_csv_auto('{nodes}') GROUP BY 1
        )
        SELECT lower(trim(CAST(c.ccLabel AS VARCHAR))) AS label,
               count(*) AS components,
               min(coalesce(n.node_count,0)) AS min_nodes,
               approx_quantile(coalesce(n.node_count,0), 0.5) AS median_nodes,
               avg(coalesce(n.node_count,0)) AS avg_nodes,
               max(coalesce(n.node_count,0)) AS max_nodes
        FROM read_csv_auto('{cc}') c
        LEFT JOIN n USING(ccId)
        GROUP BY 1 ORDER BY components DESC
        """
    ).fetchall()

    quality = con.execute(
        f"""
        WITH n AS (SELECT clId, ccId FROM read_csv_auto('{nodes}')),
        e AS (SELECT * FROM read_csv_auto('{edges}')),
        mapped AS (
          SELECT e.clId1, e.clId2, n1.ccId AS cc1, n2.ccId AS cc2
          FROM e
          LEFT JOIN n n1 ON e.clId1=n1.clId
          LEFT JOIN n n2 ON e.clId2=n2.clId
        )
        SELECT
          sum(CASE WHEN cc1 IS NULL THEN 1 ELSE 0 END) AS missing_source_nodes,
          sum(CASE WHEN cc2 IS NULL THEN 1 ELSE 0 END) AS missing_target_nodes,
          sum(CASE WHEN cc1 IS NOT NULL AND cc2 IS NOT NULL AND cc1<>cc2 THEN 1 ELSE 0 END) AS cross_component_edges
        FROM mapped
        """
    ).fetchone()

    profile = {
        "label_counts": [
            {"label": label, "components": int(count)} for label, count in label_rows
        ],
        "node_count_by_label": [
            {
                "label": row[0],
                "components": int(row[1]),
                "min_nodes": int(row[2]),
                "median_nodes": float(row[3]),
                "avg_nodes": float(row[4]),
                "max_nodes": int(row[5]),
            }
            for row in node_summary
        ],
        "edge_mapping_quality": {
            "missing_source_nodes": int(quality[0] or 0),
            "missing_target_nodes": int(quality[1] or 0),
            "cross_component_edges": int(quality[2] or 0),
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
