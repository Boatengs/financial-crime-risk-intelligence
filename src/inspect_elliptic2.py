from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED = [
    "background_edges.csv",
    "background_nodes.csv",
    "connected_components.csv",
    "edges.csv",
    "nodes.csv",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output", default="results/elliptic2_schema_manifest.json")
    args = parser.parse_args()

    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("duckdb is required: pip install -e .") from exc

    raw = Path(args.raw_dir)
    missing = [name for name in EXPECTED if not (raw / name).exists()]
    if missing:
        raise SystemExit(f"Missing Elliptic2 files: {missing}")

    con = duckdb.connect()
    manifest = {}
    for name in EXPECTED:
        path = (raw / name).as_posix()
        schema = con.execute(
            f"DESCRIBE SELECT * FROM read_csv_auto('{path}', sample_size=100000)"
        ).fetchdf()
        rows = con.execute(f"SELECT count(*) FROM read_csv_auto('{path}')").fetchone()[0]
        manifest[name] = {
            "rows": int(rows),
            "columns": schema[["column_name", "column_type"]].to_dict(orient="records"),
        }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
