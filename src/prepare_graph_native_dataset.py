from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a compact graph-native Elliptic2 dataset from the labeled subgraph universe. "
            "This scans background_nodes.csv once for the 43 node features and does not scan "
            "background_edges.csv."
        )
    )
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--nodes-output", default="data/derived/labeled_graph_nodes.parquet")
    parser.add_argument("--edges-output", default="data/derived/labeled_graph_edges.parquet")
    parser.add_argument(
        "--components-output", default="data/derived/labeled_graph_components.parquet"
    )
    parser.add_argument(
        "--profile-output", default="results/graph_native/graph_dataset_profile.json"
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
    components = raw / "connected_components.csv"
    background_nodes = raw / "background_nodes.csv"
    required = [labeled_nodes, labeled_edges, components, background_nodes]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required Elliptic2 files: {missing}")

    nodes_output = Path(args.nodes_output)
    edges_output = Path(args.edges_output)
    components_output = Path(args.components_output)
    profile_output = Path(args.profile_output)
    for path in (nodes_output, edges_output, components_output, profile_output):
        path.parent.mkdir(parents=True, exist_ok=True)

    temp = Path(args.temp_dir)
    temp.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute(f"SET memory_limit='{args.memory_limit}'")
    con.execute(f"SET threads={args.threads}")
    con.execute(f"SET temp_directory='{temp.as_posix()}'")

    background_path = background_nodes.as_posix()
    node_path = labeled_nodes.as_posix()
    edge_path = labeled_edges.as_posix()
    component_path = components.as_posix()

    schema = con.execute(
        f"DESCRIBE SELECT * FROM read_csv_auto('{background_path}', sample_size=100000)"
    ).fetchall()
    background_columns = [row[0] for row in schema]
    if "clId" not in background_columns:
        raise SystemExit("Expected clId in background_nodes.csv")
    feature_columns = [column for column in background_columns if column.startswith("feat#")]
    if len(feature_columns) != 43:
        raise SystemExit(
            f"Expected 43 node feature columns in background_nodes.csv; found {len(feature_columns)}"
        )

    con.execute(
        f"""
        CREATE TEMP TABLE labeled_nodes AS
        SELECT CAST(clId AS BIGINT) AS node_id,
               CAST(ccId AS BIGINT) AS component_id
        FROM read_csv_auto('{node_path}')
        """
    )
    labeled_node_rows, distinct_labeled_nodes = con.execute(
        "SELECT count(*), count(DISTINCT node_id) FROM labeled_nodes"
    ).fetchone()

    # One full scan of background_nodes.csv. Keep only the labeled-node universe.
    feature_select = ",\n               ".join(
        f"CAST(b.{ident(feature)} AS DOUBLE) AS node_feat_{index:02d}"
        for index, feature in enumerate(feature_columns, start=1)
    )
    con.execute(
        f"""
        COPY (
          SELECT l.node_id,
                 l.component_id,
                 {feature_select}
          FROM read_csv_auto('{background_path}', sample_size=100000) b
          INNER JOIN labeled_nodes l ON CAST(b.clId AS BIGINT) = l.node_id
        ) TO '{nodes_output.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )

    matched_node_rows, distinct_matched_nodes = con.execute(
        f"SELECT count(*), count(DISTINCT node_id) FROM read_parquet('{nodes_output.as_posix()}')"
    ).fetchone()
    missing_labeled_nodes = int(distinct_labeled_nodes - distinct_matched_nodes)
    duplicate_background_matches = int(matched_node_rows - distinct_matched_nodes)

    # Validate labeled edges against the node-to-component mapping and persist only clean edges.
    con.execute(
        f"""
        CREATE TEMP TABLE labeled_edges AS
        SELECT CAST(clId1 AS BIGINT) AS source_node_id,
               CAST(clId2 AS BIGINT) AS target_node_id,
               CAST(txId AS BIGINT) AS transaction_id
        FROM read_csv_auto('{edge_path}')
        """
    )
    labeled_edge_rows = con.execute("SELECT count(*) FROM labeled_edges").fetchone()[0]
    missing_source = con.execute(
        """
        SELECT count(*)
        FROM labeled_edges e LEFT JOIN labeled_nodes n ON e.source_node_id = n.node_id
        WHERE n.node_id IS NULL
        """
    ).fetchone()[0]
    missing_target = con.execute(
        """
        SELECT count(*)
        FROM labeled_edges e LEFT JOIN labeled_nodes n ON e.target_node_id = n.node_id
        WHERE n.node_id IS NULL
        """
    ).fetchone()[0]
    cross_component = con.execute(
        """
        SELECT count(*)
        FROM labeled_edges e
        JOIN labeled_nodes s ON e.source_node_id = s.node_id
        JOIN labeled_nodes t ON e.target_node_id = t.node_id
        WHERE s.component_id <> t.component_id
        """
    ).fetchone()[0]

    con.execute(
        f"""
        COPY (
          SELECT e.transaction_id,
                 e.source_node_id,
                 e.target_node_id,
                 s.component_id
          FROM labeled_edges e
          JOIN labeled_nodes s ON e.source_node_id = s.node_id
          JOIN labeled_nodes t ON e.target_node_id = t.node_id
          WHERE s.component_id = t.component_id
        ) TO '{edges_output.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    output_edge_rows = con.execute(
        f"SELECT count(*) FROM read_parquet('{edges_output.as_posix()}')"
    ).fetchone()[0]

    con.execute(
        f"""
        COPY (
          SELECT CAST(ccId AS BIGINT) AS component_id,
                 CASE
                   WHEN lower(trim(CAST(ccLabel AS VARCHAR))) IN ('suspicious', 'illicit', '1', 'true') THEN 1
                   WHEN lower(trim(CAST(ccLabel AS VARCHAR))) IN ('licit', 'non-suspicious', 'nonsuspicious', '0', 'false') THEN 0
                   ELSE NULL
                 END AS label
          FROM read_csv_auto('{component_path}')
        ) TO '{components_output.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    component_rows, positive_components, null_labels = con.execute(
        f"""
        SELECT count(*), sum(label), count(*) FILTER (WHERE label IS NULL)
        FROM read_parquet('{components_output.as_posix()}')
        """
    ).fetchone()

    profile = {
        "status": "graph_dataset_preparation_complete",
        "labeled_node_rows": int(labeled_node_rows),
        "distinct_labeled_nodes": int(distinct_labeled_nodes),
        "matched_node_rows": int(matched_node_rows),
        "distinct_matched_nodes": int(distinct_matched_nodes),
        "missing_labeled_nodes": missing_labeled_nodes,
        "duplicate_background_matches": duplicate_background_matches,
        "node_feature_count": len(feature_columns),
        "labeled_edge_rows": int(labeled_edge_rows),
        "output_edge_rows": int(output_edge_rows),
        "missing_source_nodes": int(missing_source),
        "missing_target_nodes": int(missing_target),
        "cross_component_edges": int(cross_component),
        "component_rows": int(component_rows),
        "positive_components": int(positive_components or 0),
        "null_component_labels": int(null_labels),
        "nodes_output": nodes_output.as_posix(),
        "edges_output": edges_output.as_posix(),
        "components_output": components_output.as_posix(),
        "scope_note": (
            "Graph-native benchmark uses the labeled subgraph universe and 43 node features. "
            "It does not use the 196.2M-row background edge graph and is not a reproduction of GLASS."
        ),
    }
    profile_output.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    hard_failures = (
        missing_labeled_nodes
        + duplicate_background_matches
        + int(missing_source)
        + int(missing_target)
        + int(cross_component)
        + int(null_labels)
    )
    if hard_failures:
        raise SystemExit(
            f"Graph dataset integrity failed. Review {profile_output} before graph training."
        )
    if int(output_edge_rows) != int(labeled_edge_rows):
        raise SystemExit(
            f"Expected {int(labeled_edge_rows):,} graph edges; wrote {int(output_edge_rows):,}."
        )

    print(
        f"Wrote graph-native dataset: {int(matched_node_rows):,} nodes, "
        f"{int(output_edge_rows):,} edges, {int(component_rows):,} components, "
        f"{len(feature_columns)} node features"
    )
    print(f"Wrote {profile_output}")


if __name__ == "__main__":
    main()
