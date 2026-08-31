from __future__ import annotations

import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Build structural Elliptic2 component features.")
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output", default="data/derived/component_features.parquet")
    parser.add_argument("--memory-limit", default="4GB")
    parser.add_argument("--threads", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--temp-dir", default="data/derived/duckdb_tmp")
    args = parser.parse_args()

    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("duckdb is required: pip install -e .") from exc

    raw = Path(args.raw_dir)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(args.temp_dir)
    temp.mkdir(parents=True, exist_ok=True)

    required = ["connected_components.csv", "nodes.csv", "edges.csv"]
    missing = [name for name in required if not (raw / name).exists()]
    if missing:
        raise SystemExit(f"Missing Elliptic2 files: {missing}")

    cc_path = (raw / "connected_components.csv").as_posix()
    node_path = (raw / "nodes.csv").as_posix()
    edge_path = (raw / "edges.csv").as_posix()

    con = duckdb.connect()
    con.execute(f"SET memory_limit='{args.memory_limit}'")
    con.execute(f"SET threads={args.threads}")
    con.execute(f"SET temp_directory='{temp.as_posix()}'")

    query = f"""
    COPY (
      WITH cc AS (
        SELECT
          CAST(ccId AS BIGINT) AS component_id,
          CASE
            WHEN lower(trim(CAST(ccLabel AS VARCHAR))) IN ('illicit','suspicious','1','true') THEN 1
            WHEN lower(trim(CAST(ccLabel AS VARCHAR))) IN ('licit','non-suspicious','nonsuspicious','0','false') THEN 0
            ELSE NULL
          END AS label
        FROM read_csv_auto('{cc_path}')
      ),
      n AS (
        SELECT CAST(clId AS BIGINT) AS clId, CAST(ccId AS BIGINT) AS component_id
        FROM read_csv_auto('{node_path}')
      ),
      e AS (
        SELECT CAST(clId1 AS BIGINT) AS clId1,
               CAST(clId2 AS BIGINT) AS clId2,
               CAST(txId AS BIGINT) AS txId
        FROM read_csv_auto('{edge_path}')
      ),
      edge_cc AS (
        SELECT e.*, n1.component_id AS component_id, n2.component_id AS target_component_id
        FROM e
        LEFT JOIN n n1 ON e.clId1 = n1.clId
        LEFT JOIN n n2 ON e.clId2 = n2.clId
      ),
      valid_edges AS (
        SELECT * FROM edge_cc
        WHERE component_id IS NOT NULL
          AND target_component_id = component_id
      ),
      out_deg AS (
        SELECT component_id, clId1 AS clId, count(*) AS out_degree
        FROM valid_edges GROUP BY 1,2
      ),
      in_deg AS (
        SELECT component_id, clId2 AS clId, count(*) AS in_degree
        FROM valid_edges GROUP BY 1,2
      ),
      node_degree AS (
        SELECT n.component_id, n.clId,
               coalesce(i.in_degree, 0) AS in_degree,
               coalesce(o.out_degree, 0) AS out_degree,
               coalesce(i.in_degree, 0) + coalesce(o.out_degree, 0) AS total_degree
        FROM n
        LEFT JOIN in_deg i USING(component_id, clId)
        LEFT JOIN out_deg o USING(component_id, clId)
      ),
      node_agg AS (
        SELECT component_id,
               count(*) AS node_count,
               avg(in_degree) AS avg_in_degree,
               max(in_degree) AS max_in_degree,
               stddev_pop(in_degree) AS sd_in_degree,
               avg(out_degree) AS avg_out_degree,
               max(out_degree) AS max_out_degree,
               stddev_pop(out_degree) AS sd_out_degree,
               avg(total_degree) AS avg_total_degree,
               max(total_degree) AS max_total_degree,
               stddev_pop(total_degree) AS sd_total_degree,
               sum(CASE WHEN in_degree = 0 AND out_degree > 0 THEN 1 ELSE 0 END) AS source_nodes,
               sum(CASE WHEN out_degree = 0 AND in_degree > 0 THEN 1 ELSE 0 END) AS sink_nodes,
               sum(CASE WHEN total_degree = 0 THEN 1 ELSE 0 END) AS isolate_nodes
        FROM node_degree GROUP BY 1
      ),
      pair_agg AS (
        SELECT component_id, count(*) AS unique_directed_pairs
        FROM (SELECT DISTINCT component_id, clId1, clId2 FROM valid_edges)
        GROUP BY 1
      ),
      edge_agg AS (
        SELECT component_id,
               count(*) AS edge_count,
               count(DISTINCT txId) AS transaction_count,
               sum(CASE WHEN clId1 = clId2 THEN 1 ELSE 0 END) AS self_loop_count
        FROM valid_edges GROUP BY 1
      )
      SELECT
        cc.component_id,
        cc.label,
        coalesce(n.node_count, 0) AS node_count,
        coalesce(e.edge_count, 0) AS edge_count,
        coalesce(e.transaction_count, 0) AS transaction_count,
        coalesce(p.unique_directed_pairs, 0) AS unique_directed_pairs,
        coalesce(e.self_loop_count, 0) AS self_loop_count,
        coalesce(n.avg_in_degree, 0) AS avg_in_degree,
        coalesce(n.max_in_degree, 0) AS max_in_degree,
        coalesce(n.sd_in_degree, 0) AS sd_in_degree,
        coalesce(n.avg_out_degree, 0) AS avg_out_degree,
        coalesce(n.max_out_degree, 0) AS max_out_degree,
        coalesce(n.sd_out_degree, 0) AS sd_out_degree,
        coalesce(n.avg_total_degree, 0) AS avg_total_degree,
        coalesce(n.max_total_degree, 0) AS max_total_degree,
        coalesce(n.sd_total_degree, 0) AS sd_total_degree,
        coalesce(n.source_nodes, 0) AS source_nodes,
        coalesce(n.sink_nodes, 0) AS sink_nodes,
        coalesce(n.isolate_nodes, 0) AS isolate_nodes,
        CASE WHEN coalesce(n.node_count, 0) > 0
             THEN coalesce(e.edge_count, 0)::DOUBLE / n.node_count ELSE 0 END AS edges_per_node,
        CASE WHEN coalesce(n.node_count, 0) > 1
             THEN coalesce(p.unique_directed_pairs, 0)::DOUBLE / (n.node_count * (n.node_count - 1))
             ELSE 0 END AS directed_density
      FROM cc
      LEFT JOIN node_agg n USING(component_id)
      LEFT JOIN edge_agg e USING(component_id)
      LEFT JOIN pair_agg p USING(component_id)
      WHERE cc.label IS NOT NULL
    ) TO '{out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(query)

    rows = con.execute(f"SELECT count(*) FROM read_parquet('{out.as_posix()}')").fetchone()[0]
    positives = con.execute(
        f"SELECT sum(label) FROM read_parquet('{out.as_posix()}')"
    ).fetchone()[0]
    print(f"Wrote {out} ({rows:,} components; {int(positives or 0):,} positive labels)")


if __name__ == "__main__":
    main()
