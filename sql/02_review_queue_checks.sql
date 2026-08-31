-- Review-queue QA template.
-- Confirm descending score order, unique component IDs, and valid probability range.

SELECT count(*) AS rows, count(DISTINCT component_id) AS distinct_components
FROM investigator_queue;

SELECT min(risk_score) AS min_score, max(risk_score) AS max_score
FROM investigator_queue;
