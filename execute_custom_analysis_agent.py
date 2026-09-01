#!/usr/bin/env python
# coding: utf-8

"""
Custom Analysis Agent
Performs rigorous statistical hypothesis testing, key driver analysis,
and sandboxed analytical computation using DuckDB + Pandas DataEngine and Scipy.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats
from engine.data_engine import DataEngine
from llm.llm_gateway import LLMGateway
from models.schemas import CustomAnalysisResult, HypothesisTestResult

logger = logging.getLogger(__name__)


class CustomAnalysisAgent:
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

    def run_automated_hypothesis_tests(self) -> List[HypothesisTestResult]:
        """Runs standard statistical significance tests across numeric variables."""
        test_results: List[HypothesisTestResult] = []
        numeric_df = self.engine.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return test_results

        # 1. Normality Test (D'Agostino's K-squared test)
        for col in numeric_df.columns[:3]:
            series = numeric_df[col].dropna()
            if len(series) >= 20:
                stat_val, p_val = stats.normaltest(series)
                is_norm = p_val > 0.05
                test_results.append(HypothesisTestResult(
                    test_name=f"Normality Test (D'Agostino-Pearson): {col}",
                    columns_tested=[col],
                    statistic=round(float(stat_val), 4),
                    p_value=round(float(p_val), 6),
                    is_significant=not is_norm,
                    interpretation=f"{col} is {'normally distributed (p > 0.05)' if is_norm else 'significantly non-normal (p <= 0.05)'}."
                ))

        # 2. Binary Segment Difference Test (Two-sample T-test / Welch's)
        # Check if there is a binary target column (like target, sex, churn, etc.)
        binary_cols = [c for c in self.engine.df.columns if self.engine.df[c].dropna().nunique() == 2]
        if binary_cols and numeric_df.shape[1] > 1:
            b_col = binary_cols[0]
            val1, val2 = self.engine.df[b_col].dropna().unique()[:2]
            
            # Test a continuous metric across the 2 groups
            for num_col in numeric_df.columns:
                if num_col != b_col and numeric_df[num_col].nunique() > 5:
                    group1 = self.engine.df[self.engine.df[b_col] == val1][num_col].dropna()
                    group2 = self.engine.df[self.engine.df[b_col] == val2][num_col].dropna()
                    if len(group1) > 5 and len(group2) > 5:
                        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
                        sig = p_val < 0.05
                        test_results.append(HypothesisTestResult(
                            test_name=f"Welch's Two-Sample T-Test: {num_col} across {b_col}",
                            columns_tested=[num_col, b_col],
                            statistic=round(float(t_stat), 4),
                            p_value=round(float(p_val), 6),
                            is_significant=sig,
                            interpretation=(
                                f"Significant difference detected in {num_col} between {b_col}={val1} and {b_col}={val2} (p < 0.05)."
                                if sig else f"No statistically significant difference detected in {num_col} across {b_col} groups (p >= 0.05)."
                            )
                        ))
                    break

        return test_results

    def compute_key_drivers(self) -> List[Dict[str, Any]]:
        """Computes feature influence ranking toward the target or primary numeric column."""
        numeric_df = self.engine.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return []

        # Target selection: column named target, outcome, label, or last column
        target_col = None
        for c in numeric_df.columns:
            if c.lower() in ["target", "label", "outcome", "y", "churn", "price"]:
                target_col = c
                break
        if not target_col:
            target_col = numeric_df.columns[-1]

        corr_series = numeric_df.corr()[target_col].drop(target_col).abs().sort_values(ascending=False)
        drivers = []
        for col_name, score in corr_series.head(6).items():
            drivers.append({
                "feature": col_name,
                "target": target_col,
                "importance_score": round(float(score), 3),
                "direction": "positive" if numeric_df[target_col].corr(numeric_df[col_name]) > 0 else "negative"
            })
        return drivers

    def execute_custom_analysis(self, custom_code: Optional[str] = None) -> CustomAnalysisResult:
        """
        Executes automated statistical tests, key driver analysis, and optional sandboxed Python code.
        """
        logger.info(f"Executing statistical analysis for {self.engine.dataset_name}...")
        test_results = self.run_automated_hypothesis_tests()
        key_drivers = self.compute_key_drivers()
        executed_queries = []

        code_output = ""
        if custom_code and custom_code.strip():
            # Sandboxed execution environment
            restricted_globals = {
                "__builtins__": {
                    "abs": abs, "min": min, "max": max, "len": len, "sum": sum,
                    "round": round, "print": lambda *args: None, "range": range, "dict": dict, "list": list
                },
                "df": self.engine.df.copy(),
                "np": np,
                "pd": pd,
                "stats": stats,
            }
            local_dict = {}
            try:
                exec(custom_code, restricted_globals, local_dict)
                code_output = f"Custom code executed successfully. Result keys: {list(local_dict.keys())}"
                executed_queries.append("custom_python_execution")
            except Exception as e:
                code_output = f"Code execution failed: {str(e)}"

        prompt = f"""
Dataset: {self.engine.dataset_name}
Hypothesis Tests Conducted:
{json.dumps([t.model_dump() for t in test_results], indent=2)}

Key Driver Rankings:
{json.dumps(key_drivers, indent=2)}

Custom Code Output (if any):
{code_output}

Generate a concise, high-level analytical summary:
1. Executive summary of statistical hypothesis findings.
2. Interpretation of the primary key drivers.
3. 3 to 4 actionable recommendations for feature engineering or model training.
"""
        system_prompt = (
            "You are a Lead Data Scientist and Biostatistician. "
            "Synthesize formal statistical testing and key driver scores into unambiguous business guidance."
        )

        def mock_fallback() -> CustomAnalysisResult:
            return CustomAnalysisResult(
                summary=(
                    f"Statistical testing confirmed significant variance across primary cohort features. "
                    f"Top key driver towards outcomes is '{key_drivers[0]['feature'] if key_drivers else 'unknown'}'."
                ),
                statistical_findings=test_results,
                key_drivers=key_drivers,
                executed_queries=["SELECT * FROM data", "compute_correlation_matrix()"],
                actionable_recommendations=[
                    "Prioritize top drivers in downstream classification / regression models.",
                    "Apply robust transforms to non-normal continuous features.",
                    "Segment high-leverage outliers into isolated monitoring cohorts."
                ]
            )

        result = self.llm.generate_structured(
            prompt=prompt,
            system_prompt=system_prompt,
            response_model=CustomAnalysisResult,
            mock_fallback_factory=mock_fallback,
        )

        result.statistical_findings = test_results
        result.key_drivers = key_drivers
        return result

    def save_output(self, output_path: str = "custom_analysis_output.json") -> Dict[str, Any]:
        """Save the agent output to a JSON file."""
        result = self.execute_custom_analysis()
        result_dict = result.model_dump()
        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)
        logger.info(f"Custom analysis saved to {output_path}")
        return result_dict

    def cleanup(self):
        """Cleanup resources."""
        pass


if __name__ == "__main__":
    agent = CustomAnalysisAgent("heart.csv" if os.path.exists("heart.csv") else "dataset_description_output.json")
    print(agent.save_output())
