import pytest
from agents.data_analyzer import DataAnalyzer

def test_analyze_returns_dict():
    analyzer = DataAnalyzer()
    result = analyzer.analyze("data/test_data.csv")
    assert isinstance(result, dict)
    # basic keys
    assert "rows" in result
    assert "columns" in result
    assert "insights" in result
    # should have at least one insight
    assert len(result["insights"]) > 0