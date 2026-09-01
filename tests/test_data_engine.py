import pytest
import os
from engine.data_engine import DataEngine


def test_data_engine_loading_and_stats():
    csv_path = "sample_data/heart_disease.csv"
    assert os.path.exists(csv_path), "Sample CSV file must exist"

    engine = DataEngine(csv_path)
    assert engine.total_rows > 0
    assert engine.total_columns == 14
    assert "age" in engine.column_names

    # Check stats
    stats = engine.get_column_statistics()
    assert "age" in stats
    age_stat = stats["age"]
    assert age_stat.null_count == 0
    assert age_stat.mean_val is not None
    assert age_stat.semantic_type in ["numeric_metric", "categorical"]


def test_correlation_and_anomalies():
    engine = DataEngine("sample_data/heart_disease.csv")
    corr_matrix, notable = engine.get_correlation_matrix()
    assert isinstance(corr_matrix, dict)
    assert isinstance(notable, list)

    anomalies = engine.detect_outliers_and_anomalies()
    assert "duplicate_count" in anomalies
    assert "outlier_counts" in anomalies


def test_sql_execution():
    engine = DataEngine("sample_data/heart_disease.csv")
    res = engine.execute_sql("SELECT age, trestbps FROM data WHERE age > 60 LIMIT 5")
    assert res["success"] is True
    assert len(res["rows"]) <= 5
    assert "age" in res["columns"]

    # Test safety guard
    with pytest.raises(ValueError):
        engine.execute_sql("DROP TABLE data")
