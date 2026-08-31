import pandas as pd

from financial_crime_risk_intelligence.features import component_structural_features


def test_component_features():
    nodes = pd.DataFrame({"component_id": ["A", "A", "A"], "node_id": ["1", "2", "3"]})
    edges = pd.DataFrame({"component_id": ["A", "A"], "source": ["1", "2"], "target": ["2", "3"]})
    result = component_structural_features(nodes, edges).iloc[0]
    assert result["node_count"] == 3
    assert result["edge_count"] == 2
    assert result["max_degree"] == 2
