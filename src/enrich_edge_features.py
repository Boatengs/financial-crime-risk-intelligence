from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Join the 367k labeled Elliptic2 edges to the 196.2M-row background edge "
            "table and aggregate all 95 edge features by connected component."
        )
    )
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument(
        "--node-enriched-input",
        default="data/derived/component_features_node_enriched.parquet",
    )
    parser.add_argument(
        "--output",
        default="data/derived/component_features_node_edge_enriched.parquet",
    )
    parser.add_argument(
        "--profile-output",
        default="results/edge_feature_enrichment_profile.json",
    )
    parser.add_argument("--memory-limit", default="4GB")
    parser.add_argument("--threads", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--temp-dir", default="data/derived/duckdb_tmp")
    args = parser.parse_args()

    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("duckdb is required: pip install -e .") from exc

    raw = Path(args.raw_dir)
    labeled_nodes = raw / "nodes.csv"
    labeled_edges = raw / "edges.csv"
    background_edges = raw / "background_edges.csv"
    node_enriched = Path(args.node_enriched_input)
    output = Path(args.output)
    profile_output = Path(args.profile_output)

    missing_files = [
        p
        for p in (labeled_nodes, labeled_edges, background_edges, node_enriched)
        if not p.exists()
    ]
    if missing_files:
        raise SystemExit(f"Missing required files: {[str(p) for p in missing_files]}")

    output.parent.mkdir(parents=True, exist_ok=True)
    profile_output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(args.temp_dir)
    temp.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute(f"SET memory_limit='{args.memory_limit}'")
    con.execute(f"SET threads={args.threads}")
    con.execute(f"SET temp_directory='{temp.as_posix()}'")
    con.execute("SET preserve_insertion_order=false")

    nodes_path = labeled_nodes.as_posix()
    labeled_edges_path = labeled_edges.as_posix()
    background_edges_path = background_edges.as_posix()
    node_enriched_path = node_enriched.as_posix()

    background_schema = con.execute(
        f"DESCRIBE SELECT * FROM read_csv_auto('{background_edges_path}', sample_size=100000)"
    ).fetchall()
    background_columns = [row[0] for row in background_schema]
    required_background = {"clId1", "clId2", "txId"}
    if not required_background.issubset(background_columns):
        missing = sorted(required_background - set(background_columns))
        raise SystemExit(f"Missing expected background-edge key columns: {missing}")

    feature_columns = [c for c in background_columns if c.startswith("feat#")]
    if len(feature_columns) != 95:
        raise SystemExit(
            f"Expected 95 edge feature columns in background_edges.csv; found {len(feature_columns)}"
        )

    # Map each labeled edge to its already-validated connected component using
    # the source node. Earlier graph-integrity checks confirmed zero missing
    # endpoints and zero cross-component labeled edges.
    con.execute(
        f"""
        CREATE TEMP TABLE labeled_edges AS
        WITH n AS (
          SELECT CAST(clId AS BIGINT) AS clId, CAST(ccId AS BIGINT) AS component_id
          FROM read_csv_auto('{nodes_path}')
        )
        SELECT
          CAST(e.clId1 AS BIGINT) AS clId1,
          CAST(e.clId2 AS BIGINT) AS clId2,
          CAST(e.txId AS BIGINT) AS txId,
          n.component_id
        FROM read_csv_auto('{labeled_edges_path}') e
        LEFT JOIN n ON CAST(e.clId1 AS BIGINT) = n.clId
        """
    )

    labeled_count = con.execute("SELECT count(*) FROM labeled_edges").fetchone()[0]
    labeled_distinct = con.execute(
        "SELECT count(*) FROM (SELECT DISTINCT clId1, clId2, txId FROM labeled_edges)"
    ).fetchone()[0]
    missing_component_ids = con.execute(
        "SELECT count(*) FROM labeled_edges WHERE component_id IS NULL"
    ).fetchone()[0]

    # The expensive step: one full scan of the 196.2M-row background-edge CSV.
    # The small labeled-edge key table is used as the join side so only the
    # labeled universe is retained after the scan.
    print("Scanning background_edges.csv and matching labeled edge keys...")
    con.execute(
        f"""
        CREATE TEMP TABLE matched_edge_features AS
        SELECT l.component_id, b.*
        FROM read_csv_auto('{background_edges_path}', sample_size=100000) b
        INNER JOIN labeled_edges l
          ON CAST(b.clId1 AS BIGINT) = l.clId1
         AND CAST(b.clId2 AS BIGINT) = l.clId2
         AND CAST(b.txId AS BIGINT) = l.txId
        """
    )

    matched_count = con.execute("SELECT count(*) FROM matched_edge_features").fetchone()[0]
    matched_distinct = con.execute(
        "SELECT count(*) FROM (SELECT DISTINCT clId1, clId2, txId FROM matched_edge_features)"
    ).fetchone()[0]

    duplicate_labeled_keys = int(labeled_count - labeled_distinct)
    missing_labeled_edges = int(labeled_distinct - matched_distinct)
    duplicate_background_matches = int(matched_count - matched_distinct)

    profile = {
        "labeled_edge_rows": int(labeled_count),
        "distinct_labeled_edge_keys": int(labeled_distinct),
        "duplicate_labeled_edge_keys": duplicate_labeled_keys,
        "missing_component_ids": int(missing_component_ids),
        "matched_background_rows": int(matched_count),
        "distinct_matched_edge_keys": int(matched_distinct),
        "missing_labeled_edges": missing_labeled_edges,
        "duplicate_background_matches": duplicate_background_matches,
        "source_edge_feature_count": len(feature_columns),
        "aggregations_per_feature": ["mean", "stddev_pop", "min", "max"],
        "aggregate_edge_feature_count": len(feature_columns) * 4,
    }
    profile_output.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    if (
        duplicate_labeled_keys
        or missing_component_ids
        or missing_labeled_edges
        or duplicate_background_matches
    ):
        raise SystemExit(
            "Edge-feature match integrity failed. Review "
            f"{profile_output} before training edge-enriched models."
        )

    aggregate_exprs: list[str] = []
    aggregate_aliases: list[str] = []
    for index, feature in enumerate(feature_columns, start=1):
        source = ident(feature)
        prefix = f"edge_feat_{index:02d}"
        for function, suffix in (
            ("avg", "mean"),
            ("stddev_pop", "sd"),
            ("min", "min"),
            ("max", "max"),
        ):
            alias = f"{prefix}_{suffix}"
            aggregate_exprs.append(f"{function}({source}) AS {ident(alias)}")
            aggregate_aliases.append(alias)

    aggregate_sql = ",\n               ".join(aggregate_exprs)
    # Components without matched edges keep an explicit coverage count of zero;
    # their edge-derived numeric features are zero-filled so downstream sklearn
    # baselines receive a complete numeric matrix rather than NaNs.
    enriched_columns = ",\n        ".join(
        f"coalesce(a.{ident(c)}, 0) AS {ident(c)}" for c in aggregate_aliases
    )

    query = f"""
    COPY (
      WITH edge_agg AS (
        SELECT component_id,
               count(*) AS matched_edge_count,
               {aggregate_sql}
        FROM matched_edge_features
        GROUP BY component_id
      )
      SELECT
        s.*,
        coalesce(a.matched_edge_count, 0) AS matched_edge_count,
        {enriched_columns}
      FROM read_parquet('{node_enriched_path}') s
      LEFT JOIN edge_agg a USING(component_id)
    ) TO '{output.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(query)

    output_rows, positives = con.execute(
        f"SELECT count(*), sum(label) FROM read_parquet('{output.as_posix()}')"
    ).fetchone()
    components_without_edge_features = con.execute(
        f"""
        SELECT count(*)
        FROM read_parquet('{output.as_posix()}')
        WHERE matched_edge_count = 0
        """
    ).fetchone()[0]
    null_aggregate_rows = con.execute(
        f"""
        SELECT count(*)
        FROM read_parquet('{output.as_posix()}')
        WHERE edge_feat_01_mean IS NULL
        """
    ).fetchone()[0]

    profile.update(
        {
            "output_component_rows": int(output_rows),
            "positive_component_rows": int(positives or 0),
            "components_without_edge_features": int(components_without_edge_features),
            "rows_with_null_edge_aggregates": int(null_aggregate_rows),
            "output": output.as_posix(),
        }
    )
    profile_output.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    print(
        f"Wrote {output} ({output_rows:,} components; "
        f"{int(positives or 0):,} positive labels; "
        f"{len(aggregate_aliases)} aggregated edge features)"
    )
    print(f"Wrote {profile_output}")


if __name__ == "__main__":
    main()
