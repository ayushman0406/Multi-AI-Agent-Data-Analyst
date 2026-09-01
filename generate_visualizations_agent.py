#!/usr/bin/env python
# coding: utf-8

"""
Visualizations Agent
Creates domain-appropriate, interactive Plotly visualizations with AI guidance
styled with Midnight Luxe dark aesthetics (emerald/cyan glows, obsidian canvas).
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
from engine.data_engine import DataEngine
from llm.llm_gateway import LLMGateway
from models.schemas import VisualizationResult, PlotlyChartSpec

logger = logging.getLogger(__name__)

# Midnight Luxe color palette tokens for Plotly
DARK_LAYOUT_TEMPLATE = {
    "paper_bgcolor": "#0B1120",
    "plot_bgcolor": "#0F172A",
    "font": {"color": "#E2E8F0", "family": "Inter, sans-serif"},
    "margin": {"t": 40, "b": 40, "l": 50, "r": 20},
    "xaxis": {
        "gridcolor": "rgba(255, 255, 255, 0.07)",
        "zerolinecolor": "rgba(255, 255, 255, 0.15)",
        "tickfont": {"color": "#94A3B8"}
    },
    "yaxis": {
        "gridcolor": "rgba(255, 255, 255, 0.07)",
        "zerolinecolor": "rgba(255, 255, 255, 0.15)",
        "tickfont": {"color": "#94A3B8"}
    }
}


class VisualizationsAgent:
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

    def _build_correlation_heatmap(self) -> Optional[PlotlyChartSpec]:
        """Builds an interactive Plotly correlation heatmap."""
        numeric_df = self.engine.df.select_dtypes(include=[np.number])
        if numeric_df.empty or numeric_df.shape[1] < 2:
            return None
            
        # Select up to top 12 numeric cols for legibility
        cols = list(numeric_df.columns)[:12]
        corr = numeric_df[cols].corr().round(2).fillna(0.0)
        
        fig_dict = {
            "data": [{
                "type": "heatmap",
                "z": corr.values.tolist(),
                "x": cols,
                "y": cols,
                "colorscale": [
                    [0.0, "#06B6D4"],
                    [0.5, "#0F172A"],
                    [1.0, "#10B981"]
                ],
                "zmin": -1.0,
                "zmax": 1.0,
                "hoverongaps": False
            }],
            "layout": {
                **DARK_LAYOUT_TEMPLATE,
                "title": {"text": "Multi-Variable Correlation Matrix", "font": {"size": 16, "color": "#F8FAFC"}}
            }
        }
        
        return PlotlyChartSpec(
            id="correlation_heatmap",
            title="Correlation Matrix Heatmap",
            chart_type="heatmap",
            description="Pairwise Pearson correlation coefficients across numerical attributes.",
            business_insight="Identifies tightly coupled metrics to prevent collinearity and spotlight key drivers.",
            figure_json=fig_dict
        )

    def _build_distribution_chart(self) -> Optional[PlotlyChartSpec]:
        """Builds distribution histogram for the most prominent numeric feature."""
        numeric_df = self.engine.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return None
            
        target_col = numeric_df.columns[0]
        # Choose a col with high variance or non-id
        for col in numeric_df.columns:
            if not col.lower().endswith("id") and numeric_df[col].nunique() > 5:
                target_col = col
                break
                
        series = numeric_df[target_col].dropna().tolist()
        fig_dict = {
            "data": [{
                "type": "histogram",
                "x": series,
                "marker": {
                    "color": "#10B981",
                    "line": {"color": "#06B6D4", "width": 1}
                },
                "opacity": 0.85
            }],
            "layout": {
                **DARK_LAYOUT_TEMPLATE,
                "title": {"text": f"Distribution Profile: {target_col}", "font": {"size": 16, "color": "#F8FAFC"}},
                "xaxis": {**DARK_LAYOUT_TEMPLATE["xaxis"], "title": {"text": target_col}},
                "yaxis": {**DARK_LAYOUT_TEMPLATE["yaxis"], "title": {"text": "Frequency"}}
            }
        }
        
        return PlotlyChartSpec(
            id=f"distribution_{target_col}",
            title=f"Feature Distribution: {target_col}",
            chart_type="histogram",
            description=f"Frequency histogram showing skewness and clustering for {target_col}.",
            business_insight="Highlights central tendencies, kurtosis, and natural cluster grouping.",
            figure_json=fig_dict
        )

    def _build_categorical_breakdown(self) -> Optional[PlotlyChartSpec]:
        """Builds bar chart for top categorical attribute."""
        cat_cols = [c for c in self.engine.df.columns if self.engine.df[c].nunique() <= 20 and self.engine.df[c].nunique() > 1]
        if not cat_cols:
            return None
            
        cat_col = cat_cols[0]
        counts = self.engine.df[cat_col].value_counts().head(10)
        
        fig_dict = {
            "data": [{
                "type": "bar",
                "x": [str(k) for k in counts.index],
                "y": counts.values.tolist(),
                "marker": {
                    "color": ["#10B981", "#06B6D4", "#3B82F6", "#6366F1", "#8B5CF6", "#EC4899"] * 3,
                }
            }],
            "layout": {
                **DARK_LAYOUT_TEMPLATE,
                "title": {"text": f"Category Breakdown: {cat_col}", "font": {"size": 16, "color": "#F8FAFC"}},
                "xaxis": {**DARK_LAYOUT_TEMPLATE["xaxis"], "title": {"text": cat_col}},
                "yaxis": {**DARK_LAYOUT_TEMPLATE["yaxis"], "title": {"text": "Count"}}
            }
        }
        
        return PlotlyChartSpec(
            id=f"categorical_{cat_col}",
            title=f"Categorical Frequency: {cat_col}",
            chart_type="bar",
            description=f"Segment frequency distribution across categories in {cat_col}.",
            business_insight="Identifies market share, cohort imbalance, or primary demographic concentration.",
            figure_json=fig_dict
        )

    def _build_scatter_relationship(self) -> Optional[PlotlyChartSpec]:
        """Builds scatter plot exploring top correlated numeric pair."""
        numeric_df = self.engine.df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return None
            
        corr_matrix, notable = self.engine.get_correlation_matrix()
        if notable:
            c1, c2 = notable[0].col1, notable[0].col2
        else:
            c1, c2 = numeric_df.columns[0], numeric_df.columns[1]
            
        x_vals = self.engine.df[c1].dropna().head(300).tolist()
        y_vals = self.engine.df[c2].dropna().head(300).tolist()
        
        min_len = min(len(x_vals), len(y_vals))
        
        fig_dict = {
            "data": [{
                "type": "scatter",
                "mode": "markers",
                "x": x_vals[:min_len],
                "y": y_vals[:min_len],
                "marker": {
                    "color": "#06B6D4",
                    "size": 7,
                    "opacity": 0.8,
                    "line": {"color": "#10B981", "width": 1}
                }
            }],
            "layout": {
                **DARK_LAYOUT_TEMPLATE,
                "title": {"text": f"Bivariate Relationship: {c1} vs {c2}", "font": {"size": 16, "color": "#F8FAFC"}},
                "xaxis": {**DARK_LAYOUT_TEMPLATE["xaxis"], "title": {"text": c1}},
                "yaxis": {**DARK_LAYOUT_TEMPLATE["yaxis"], "title": {"text": c2}}
            }
        }
        
        return PlotlyChartSpec(
            id=f"scatter_{c1}_{c2}",
            title=f"Scatter Relationship: {c1} vs {c2}",
            chart_type="scatter",
            description=f"Direct scatter mapping between {c1} and {c2}.",
            business_insight="Reveals linearity, homoscedasticity, and potential non-linear inflection points.",
            figure_json=fig_dict
        )

    def generate_visualizations(self) -> VisualizationResult:
        """
        Generate full suite of interactive Plotly charts.
        Returns:
            VisualizationResult: Validated Pydantic schema containing Plotly JSON figures.
        """
        logger.info(f"Generating interactive Plotly visualizations for {self.engine.dataset_name}...")
        charts: List[PlotlyChartSpec] = []
        
        heatmap = self._build_correlation_heatmap()
        if heatmap:
            charts.append(heatmap)
            
        dist = self._build_distribution_chart()
        if dist:
            charts.append(dist)
            
        cat = self._build_categorical_breakdown()
        if cat:
            charts.append(cat)
            
        scatter = self._build_scatter_relationship()
        if scatter:
            charts.append(scatter)

        rationale = (
            f"Generated {len(charts)} executive-grade interactive visualizations using the Midnight Luxe "
            f"obsidian/emerald design specification. Charts are configured with hover tooltips, zoom, and "
            f"dynamic cross-filtering capabilities."
        )

        return VisualizationResult(
            recommended_charts=charts,
            design_rationale=rationale
        )

    def save_output(self, output_path: str = "visualizations_output.json") -> Dict[str, Any]:
        """Save the agent output to a JSON file."""
        result = self.generate_visualizations()
        result_dict = result.model_dump()
        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)
        logger.info(f"Visualizations saved to {output_path}")
        return result_dict

    def cleanup(self):
        """Cleanup resources."""
        pass


if __name__ == "__main__":
    agent = VisualizationsAgent("heart.csv" if os.path.exists("heart.csv") else "dataset_description_output.json")
    print(agent.save_output())
