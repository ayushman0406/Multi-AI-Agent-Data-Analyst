import pytest
import os
from pipeline.orchestrator import AnalysisPipeline


def test_full_pipeline_run():
    csv_path = "sample_data/heart_disease.csv"
    assert os.path.exists(csv_path)

    pipeline = AnalysisPipeline(csv_path)
    state = pipeline.run_full_pipeline()

    assert state.total_rows > 0
    assert state.dataset_description is not None
    assert state.dataset_description.business_domain != ""
    assert state.domain_patterns is not None
    assert len(state.visualizations.recommended_charts) > 0
    assert state.custom_analysis is not None
    assert state.business_goals is not None
    assert state.comprehensive_report is not None
    assert len(state.comprehensive_report.strategic_recommendations) > 0


def test_conversational_chat():
    pipeline = AnalysisPipeline("sample_data/heart_disease.csv")
    pipeline.run_full_pipeline()

    reply = pipeline.chat_with_data("What are the primary findings in this dataset?")
    assert isinstance(reply, str)
    assert len(reply) > 20
