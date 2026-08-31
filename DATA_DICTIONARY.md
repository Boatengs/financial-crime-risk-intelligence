# Data Dictionary

The official Elliptic2 feature names are partially anonymized/binned. The project preserves the raw names and creates a canonical component-level analytical table.

## Canonical component table

| Field | Type | Meaning |
|---|---|---|
| `component_id` | string | Connected-component / labeled-subgraph identifier |
| `label` | int | 1 = suspicious, 0 = licit |
| `node_count` | int | Number of nodes in the subgraph |
| `edge_count` | int | Number of internal directed edges |
| `density` | float | Directed graph density for the subgraph |
| `mean_in_degree` | float | Mean in-degree within the subgraph |
| `mean_out_degree` | float | Mean out-degree within the subgraph |
| `max_degree` | float | Maximum total degree within the subgraph |
| `node_feature_*` | float | Aggregated anonymized node features |
| `edge_feature_*` | float | Aggregated anonymized edge features when available |

## Investigator queue

| Field | Meaning |
|---|---|
| `rank` | Review priority |
| `component_id` | Case identifier |
| `risk_score` | Model probability / normalized risk estimate |
| `risk_band` | critical / high / elevated / standard |
| `reason_1` | Primary structural or feature reason |
| `reason_2` | Secondary reason |
| `node_count` | Size of subgraph |
| `edge_count` | Number of internal edges |

Ground-truth labels must never be exposed as a production reason code; they are used only for evaluation.
