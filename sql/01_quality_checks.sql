-- Template checks for a DuckDB/Parquet component feature store.
-- Run after the canonical component_features view/table exists.

SELECT count(*) AS row_count FROM component_features;
SELECT count(*) AS missing_component_id FROM component_features WHERE component_id IS NULL;
SELECT label, count(*) AS n FROM component_features GROUP BY label ORDER BY label;
