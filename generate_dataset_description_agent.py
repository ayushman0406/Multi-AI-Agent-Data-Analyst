#!/usr/bin/env python
# coding: utf-8

"""
Dataset Description Agent
Generates comprehensive business and technical descriptions of datasets
using DuckDB + Pandas DataEngine and validated Pydantic models.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from engine.data_engine import DataEngine
from llm.llm_gateway import LLMGateway
from models.schemas import DatasetDescriptionResult, DataQualityIssue

logger = logging.getLogger(__name__)


class DatasetDescriptionAgent:
    def __init__(
        self,
        data_source: str,
        data_format: str = "csv",
        limit: Optional[int] = 1000,
        data_engine: Optional[DataEngine] = None,
        llm_gateway: Optional[LLMGateway] = None,
    ):
        self.data_source = data_source
        self.data_format = data_format
        self.limit = limit
        
        # Initialize or reuse DataEngine
        self.engine = data_engine or DataEngine(data_source, limit=limit)
        self.llm = llm_gateway or LLMGateway()

    def generate_dataset_description(self) -> DatasetDescriptionResult:
        """
        Generate comprehensive business and technical descriptions of the dataset.
        Returns:
            DatasetDescriptionResult: Validated Pydantic schema with structured insights.
        """
        logger.info(f"Analyzing dataset schema and statistics for {self.engine.dataset_name}...")
        col_stats = self.engine.get_column_statistics()
        sample_rows = self.engine.get_sample_rows(n=5)
        outlier_info = self.engine.detect_outliers_and_anomalies()

        # Build prompt for LLM
        prompt = f"""
Dataset Name: {self.engine.dataset_name}
Total Records: {self.engine.total_rows}
Total Columns: {self.engine.total_columns}

Column Summary:
{json.dumps({col: stat.model_dump() for col, stat in col_stats.items()}, indent=2, default=str)}

Sample Data (First 5 records):
{json.dumps(sample_rows, indent=2, default=str)}

Detected Data Quality Signals:
- Duplicate Rows: {outlier_info.get('duplicate_count', 0)}
- Outlier Columns: {json.dumps(outlier_info.get('outlier_counts', {}))}
- Potential Anomalies: {json.dumps(outlier_info.get('anomaly_flags', []))}

Generate a rich, expert dataset description including:
1. Business domain identification (e.g. Healthcare, Fintech, Retail, Logistics).
2. Business processes and operational workflows this dataset supports.
3. Target personas/stakeholders who rely on this data.
4. Core entities (nouns) and relationships.
5. Strategic business value of this data asset.
6. Technical description for each column (plain-English definition, intended use).
7. Specific data quality issues identified with severity and remediation.
8. Recommended data transformations or feature engineering steps.
"""
        system_prompt = (
            "You are a Senior Principal Data Analyst and Data Architect. "
            "Provide high-depth, rigorous business and technical descriptions based strictly "
            "on the provided schema and actual values."
        )

        def mock_fallback() -> DatasetDescriptionResult:
            domain = "Healthcare & Biomedical" if any("chol" in c or "age" in c or "bps" in c for c in col_stats) else "General Business Operations"
            return DatasetDescriptionResult(
                dataset_name=self.engine.dataset_name,
                business_domain=domain,
                business_processes=["Operational Monitoring", "Predictive Analytics", "Decision Support"],
                target_personas=["Executive Leadership", "Data Science Team", "Operations Managers"],
                key_entities=[self.engine.dataset_name.split('.')[0].capitalize(), "Transaction", "Observation"],
                strategic_value="Enables data-driven operational decisions and risk mitigation through automated telemetry.",
                column_descriptions={
                    col: f"Stores {stat.semantic_type} metric representing {col}."
                    for col, stat in col_stats.items()
                },
                data_quality_issues=[
                    DataQualityIssue(
                        severity="medium" if outlier_info.get("duplicate_count", 0) > 0 else "low",
                        description=f"Identified {outlier_info.get('duplicate_count', 0)} duplicate records in the sampled data.",
                        affected_columns=[],
                        recommendation="Deduplicate records on primary business keys prior to production modeling."
                    )
                ],
                recommended_transformations=[
                    "Normalize continuous numerical features using robust scaling.",
                    "Impute missing values using domain-specific median strategies."
                ],
                total_records=self.engine.total_rows,
                total_columns=self.engine.total_columns,
                column_statistics=col_stats,
            )

        result = self.llm.generate_structured(
            prompt=prompt,
            system_prompt=system_prompt,
            response_model=DatasetDescriptionResult,
            mock_fallback_factory=mock_fallback,
        )
        
        # Ensure raw stats and counts are attached
        result.dataset_name = self.engine.dataset_name
        result.total_records = self.engine.total_rows
        result.total_columns = self.engine.total_columns
        result.column_statistics = col_stats
        return result

    def save_output(self, output_path: str = "dataset_description_output.json") -> Dict[str, Any]:
        """Save the agent output to a JSON file."""
        result = self.generate_dataset_description()
        result_dict = result.model_dump()
        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)
        logger.info(f"Dataset description saved to {output_path}")
        return result_dict

    def cleanup(self):
        """Cleanup resources."""
        pass


if __name__ == "__main__":
    agent = DatasetDescriptionAgent("heart.csv" if os.path.exists("heart.csv") else "dataset_description_output.json")
    print(agent.save_output())
