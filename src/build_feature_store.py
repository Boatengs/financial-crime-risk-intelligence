from __future__ import annotations

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Build a scalable Elliptic2 feature store.")
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output", default="data/derived/component_features.parquet")
    args = parser.parse_args()

    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("duckdb is required: pip install -e .") from exc

    raw = Path(args.raw_dir)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    # The official guide confirms ccLabel, clId1 and clId2. Other identifier names
    # are validated dynamically to avoid silently assuming a schema that differs
    # from the downloaded release.
    con = duckdb.connect()
    for name in ["connected_components.csv", "nodes.csv", "edges.csv"]:
        if not (raw / name).exists():
            raise SystemExit(f"Missing {name}; run inspect_elliptic2.py first")

    cc_cols = [r[0] for r in con.execute(
        f"DESCRIBE SELECT * FROM read_csv_auto('{(raw/'connected_components.csv').as_posix()}')"
    ).fetchall()]
    node_cols = [r[0] for r in con.execute(
        f"DESCRIBE SELECT * FROM read_csv_auto('{(raw/'nodes.csv').as_posix()}')"
    ).fetchall()]

    if "ccLabel" not in cc_cols:
        raise SystemExit("Expected ccLabel not found. Review schema manifest before proceeding.")

    cc_id = next((c for c in cc_cols if c.lower() in {"ccid", "component_id", "connectedcomponent"}), cc_cols[0])
    node_cc = next((c for c in node_cols if c.lower() in {"ccid", "component_id", "connectedcomponent"}), node_cols[1] if len(node_cols) > 1 else None)
    node_id = next((c for c in node_cols if c.lower() in {"clid", "node_id", "cluster_id"}), node_cols[0])
    if node_cc is None:
        raise SystemExit("Could not infer component identifier in nodes.csv")

    cc_path = (raw / "connected_components.csv").as_posix()
    node_path = (raw / "nodes.csv").as_posix()

    # First reliable baseline: component size + labels. Feature aggregations are
    # appended after schema profiling confirms anonymized feature columns.
    query = f"""
    COPY (
      WITH cc AS (
        SELECT CAST({cc_id} AS VARCHAR) AS component_id,
               CASE WHEN lower(CAST(ccLabel AS VARCHAR)) IN ('suspicious','1','true') THEN 1 ELSE 0 END AS label
        FROM read_csv_auto('{cc_path}')
      ), n AS (
        SELECT CAST({node_cc} AS VARCHAR) AS component_id,
               count(DISTINCT {node_id}) AS node_count
        FROM read_csv_auto('{node_path}')
        GROUP BY 1
      )
      SELECT cc.component_id, cc.label, coalesce(n.node_count,0) AS node_count
      FROM cc LEFT JOIN n USING(component_id)
    ) TO '{out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(query)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
