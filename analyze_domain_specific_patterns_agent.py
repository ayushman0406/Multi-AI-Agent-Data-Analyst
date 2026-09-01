#!/usr/bin/env python
# coding: utf-8

"""
Domain-Specific Patterns Analysis Agent
Analyzes domain-specific patterns, correlations, and anomalies
using DuckDB + Pandas DataEngine and validated Pydantic models.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from engine.data_engine import DataEngine
from llm.llm_gateway import LLMGateway
from models.schemas import DomainPatternsResult, DomainPattern, CorrelationItem

logger = logging.getLogger(__name__)


class DomainSpecificPatternsAgent:
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
        
        self.engine = data_engine or DataEngine(data_source, limit=limit)
        self.llm = llm_gateway or LLMGateway()

    def analyze_domain_patterns(self, dataset_description: Optional[Any] = None) -> DomainPatternsResult:
        """
        Analyze statistical relationships, correlations, and domain-specific anomalies.
        Returns:
            DomainPatternsResult: Validated Pydantic schema with patterns and takeaways.
        """
        logger.info(f"Analyzing domain-specific patterns for {self.engine.dataset_name}...")
        corr_matrix, notable_corrs = self.engine.get_correlation_matrix()
        anomaly_info = self.engine.detect_outliers_and_anomalies()
        sample_rows = self.engine.get_sample_rows(n=5)
        
        domain_context = ""
        if dataset_description and hasattr(dataset_description, "business_domain"):
            domain_context = f"Identified Business Domain: {dataset_description.business_domain}\nEntities: {', '.join(dataset_description.key_entities)}"

        prompt = f"""
Dataset: {self.engine.dataset_name}
{domain_context}

Pairwise Significant Correlations:
{json.dumps([c.model_dump() for c in notable_corrs[:10]], indent=2)}

Anomaly and Outlier Signals:
{json.dumps(anomaly_info, indent=2)}

Sample Data Excerpt:
{json.dumps(sample_rows, indent=2, default=str)}

Based on these mathematical patterns and the business domain:
1. Identify 3 to 5 core Domain Patterns (complex cross-feature patterns or customer/operational segments).
2. Interpret the top correlations in clear business terms.
3. Detail notable anomalies detected and what risk or opportunity they represent.
4. Provide 3 executive takeaways summarizing the commercial or operational reality behind these numbers.
"""
        system_prompt = (
            "You are a Principal Quantitative Strategist and Domain Pattern Analyst. "
            "Synthesize deep statistical patterns, avoiding generic surface descriptions. "
            "Translate statistical correlations into real-world causal hypotheses and business implications."
        )

        def mock_fallback() -> DomainPatternsResult:
            patterns = [
                DomainPattern(
                    name="Core Metric Covariance",
                    description=f"Primary numeric features demonstrate coordinated variance across sampled rows.",
                    confidence="high",
                    business_implication="Operational changes to upstream features will predictably impact downstream targets."
                ),
                DomainPattern(
                    name="Outlier Concentration",
                    description=f"Outliers are concentrated in extreme values across {len(anomaly_info.get('outlier_counts', {}))} columns.",
                    confidence="medium",
                    business_implication="Requires segmented business policies for high-value tail events."
                )
            ]
            return DomainPatternsResult(
                key_patterns=patterns,
                notable_correlations=notable_corrs[:8],
                temporal_trends=None,
                anomalies_detected=anomaly_info.get("anomaly_flags", ["No critical anomalies flagged."]),
                executive_takeaways=[
                    "High correlation among core attributes suggests predictive predictability.",
                    "Outlier density necessitates outlier-resistant operational thresholds.",
                    "Data distribution indicates distinct subgroup behavior."
                ]
            )

        result = self.llm.generate_structured(
            prompt=prompt,
            system_prompt=system_prompt,
            response_model=DomainPatternsResult,
            mock_fallback_factory=mock_fallback,
        )

        # Merge calculated notable correlations if model omitted them
        if not result.notable_correlations and notable_corrs:
            result.notable_correlations = notable_corrs[:8]
        return result

    def save_output(self, output_path: str = "domain_patterns_output.json") -> Dict[str, Any]:
        """Save the agent output to a JSON file."""
        result = self.analyze_domain_patterns()
        result_dict = result.model_dump()
        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)
        logger.info(f"Domain patterns saved to {output_path}")
        return result_dict

    def cleanup(self):
        """Cleanup resources."""
        pass


if __name__ == "__main__":
    agent = DomainSpecificPatternsAgent("heart.csv" if os.path.exists("heart.csv") else "dataset_description_output.json")
    print(agent.save_output())
