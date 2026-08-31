from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def main():
    parser = argparse.ArgumentParser(
        description="Join labeled Elliptic2 nodes to the 49.3M-row background node table and aggregate 43 features by component."
    )
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument(
        "--structural-input", default="data/derived/component_features.parquet"
    )
    parser.add_argument(
        "--output", default="data/derived/component_features_node_enriched.parquet"
    )
    parser.add_argument(
        "--profile-output", default="results/node_feature_enrichment_profile.json"
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
    background_nodes = raw / "background_nodes.csv"
    structural = Path(args.structural_input)
    output = Path(args.output)
    profile_output = Path(args.profile_output)

    missing_files = [
        p for p in (labeled_nodes, background_nodes, structural) if not p.exists()
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

    labeled_path = labeled_nodes.as_posix()
    background_path = background_nodes.as_posix()
    structural_path = structural.as_posix()

    background_schema = con.execute(
        f"DESCRIBE SELECT * FROM read_csv_auto('{background_path}', sample_size=100000)"
    ).fetchall()
    background_columns = [row[0] for row in background_schema]
    if "clId" not in background_columns:
        raise SystemExit("Expected clId in background_nodes.csv")

    feature_columns = [c for c in background_columns if c.startswith("feat#")]
    if len(feature_columns) != 43:
        raise SystemExit(
            f"Expected 43 node feature columns in background_nodes.csv; found {len(feature_columns)}"
        )

    con.execute(
        f"""
        CREATE TEMP TABLE labeled_nodes AS
        SELECT CAST(clId AS BIGINT) AS clId, CAST(ccId AS BIGINT) AS component_id
        FROM read_csv_auto('{labeled_path}')
        """
    )

    labeled_count, labeled_distinct = con.execute(
        "SELECT count(*), count(DISTINCT clId) FROM labeled_nodes"
    ).fetchone()

    # This is the only full scan of the 49.3M-row background node table. The
    # inner join retains only the labeled node universe before aggregation.
    con.execute(
        f"""
        CREATE TEMP TABLE matched_node_features AS
        SELECT l.component_id, b.*
        FROM read_csv_auto('{background_path}', sample_size=100000) b
        INNER JOIN labeled_nodes l ON b.clId = l.clId
        """
    )

    matched_count, matched_distinct = con.execute(
        "SELECT count(*), count(DISTINCT clId) FROM matched_node_features"
    ).fetchone()
    missing_labeled_nodes = int(labeled_distinct - matched_distinct)
    duplicate_background_matches = int(matched_count - matched_distinct)

    profile = {
        "labeled_node_rows": int(labeled_count),
        "distinct_labeled_nodes": int(labeled_distinct),
        "matched_background_rows": int(matched_count),
        "distinct_matched_nodes": int(matched_distinct),
        "missing_labeled_nodes": missing_labeled_nodes,
        "duplicate_background_matches": duplicate_background_matches,
        "source_node_feature_count": len(feature_columns),
        "aggregations_per_feature": ["mean", "stddev_pop", "min", "max"],
        "aggregate_node_feature_count": len(feature_columns) * 4,
    }

    # Persist the match audit before refusing to continue, so any data issue can
    # be diagnosed without rerunning the 49.3M-row scan.
    profile_output.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    if missing_labeled_nodes or duplicate_background_matches:
        raise SystemExit(
            "Node-feature match integrity failed. Review "
            f"{profile_output} before training enriched models."
        )

    aggregate_exprs: list[str] = []
    aggregate_aliases: list[str] = []
    for index, feature in enumerate(feature_columns, start=1):
        source = ident(feature)
        prefix = f"node_feat_{index:02d}"
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
    enriched_columns = ",\n        ".join(f"a.{ident(c)}" for c in aggregate_aliases)

    query = f"""
    COPY (
      WITH node_agg AS (
        SELECT component_id,
               count(*) AS matched_node_count,
               {aggregate_sql}
        FROM matched_node_features
        GROUP BY component_id
      )
      SELECT
        s.*,
        a.matched_node_count,
        {enriched_columns}
      FROM read_parquet('{structural_path}') s
      LEFT JOIN node_agg a USING(component_id)
    ) TO '{output.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(query)

    output_rows, positives = con.execute(
        f"SELECT count(*), sum(label) FROM read_parquet('{output.as_posix()}')"
    ).fetchone()
    components_without_node_features = con.execute(
        f"""
        SELECT count(*)
        FROM read_parquet('{output.as_posix()}')
        WHERE matched_node_count IS NULL OR matched_node_count = 0
        """
    ).fetchone()[0]

    profile.update(
        {
            "output_component_rows": int(output_rows),
            "positive_component_rows": int(positives or 0),
            "components_without_node_features": int(components_without_node_features),
            "output": output.as_posix(),
        }
    )
    profile_output.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    print(
        f"Wrote {output} ({output_rows:,} components; "
        f"{int(positives or 0):,} positive labels; "
        f"{len(aggregate_aliases)} aggregated node features)"
    )
    print(f"Wrote {profile_output}")


if __name__ == "__main__":
    main()
