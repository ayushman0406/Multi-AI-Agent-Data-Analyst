"""
Pydantic Schemas for Multi-AI-Agent Data Analyst
Provides strict typing and validated structured outputs across all 6 agents and the pipeline.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ColumnStatistic(BaseModel):
    name: str
    data_type: str
    semantic_type: Literal[
        "id", "numeric_metric", "categorical", "datetime", "email", "currency", "text", "boolean", "unknown"
    ] = "unknown"
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    min_val: Optional[Any] = None
    max_val: Optional[Any] = None
    mean_val: Optional[float] = None
    stddev_val: Optional[float] = None
    median_val: Optional[float] = None
    top_values: Optional[List[Dict[str, Any]]] = None


class DataQualityIssue(BaseModel):
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str
    affected_columns: List[str] = Field(default_factory=list)
    recommendation: str


# ==========================================
# Agent 1: Dataset Description Result
# ==========================================
class DatasetDescriptionResult(BaseModel):
    dataset_name: str
    business_domain: str
    business_processes: List[str] = Field(default_factory=list)
    target_personas: List[str] = Field(default_factory=list)
    key_entities: List[str] = Field(default_factory=list)
    strategic_value: str
    column_descriptions: Dict[str, str] = Field(default_factory=dict)
    data_quality_issues: List[DataQualityIssue] = Field(default_factory=list)
    recommended_transformations: List[str] = Field(default_factory=list)
    total_records: int = 0
    total_columns: int = 0
    column_statistics: Dict[str, ColumnStatistic] = Field(default_factory=dict)


# ==========================================
# Agent 2: Domain Patterns Result
# ==========================================
class CorrelationItem(BaseModel):
    col1: str
    col2: str
    correlation: float
    strength: Literal["weak", "moderate", "strong", "very_strong"] = "moderate"
    interpretation: str


class DomainPattern(BaseModel):
    name: str
    description: str
    confidence: Literal["low", "medium", "high"] = "high"
    business_implication: str


class DomainPatternsResult(BaseModel):
    key_patterns: List[DomainPattern] = Field(default_factory=list)
    notable_correlations: List[CorrelationItem] = Field(default_factory=list)
    temporal_trends: Optional[List[str]] = None
    anomalies_detected: List[str] = Field(default_factory=list)
    executive_takeaways: List[str] = Field(default_factory=list)


# ==========================================
# Agent 3: Visualizations Result
# ==========================================
class PlotlyChartSpec(BaseModel):
    id: str
    title: str
    chart_type: Literal["bar", "scatter", "histogram", "heatmap", "line", "box", "pie"]
    description: str
    business_insight: str
    figure_json: Dict[str, Any] = Field(default_factory=dict)


class VisualizationResult(BaseModel):
    recommended_charts: List[PlotlyChartSpec] = Field(default_factory=list)
    design_rationale: str = ""


# ==========================================
# Agent 4: Custom Analysis Result
# ==========================================
class HypothesisTestResult(BaseModel):
    test_name: str
    columns_tested: List[str] = Field(default_factory=list)
    statistic: float
    p_value: float
    is_significant: bool
    interpretation: str


class CustomAnalysisResult(BaseModel):
    summary: str
    statistical_findings: List[HypothesisTestResult] = Field(default_factory=list)
    key_drivers: List[Dict[str, Any]] = Field(default_factory=list)
    executed_queries: List[str] = Field(default_factory=list)
    actionable_recommendations: List[str] = Field(default_factory=list)


# ==========================================
# Agent 5: Business Goals Result
# ==========================================
class BusinessGoal(BaseModel):
    category: Literal[
        "revenue_growth", "cost_reduction", "risk_mitigation", "customer_retention", "operational_efficiency"
    ] = "operational_efficiency"
    goal_title: str
    description: str
    target_metric: str
    recommended_initiatives: List[str] = Field(default_factory=list)
    estimated_impact: Literal["low", "medium", "high", "transformative"] = "high"


class BusinessGoalsResult(BaseModel):
    strategic_goals: List[BusinessGoal] = Field(default_factory=list)
    revenue_optimizations: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    priority_action_matrix: List[Dict[str, str]] = Field(default_factory=list)


# ==========================================
# Agent 6: Comprehensive Report Result
# ==========================================
class StrategicRecommendation(BaseModel):
    pillar: str
    priority: Literal["Immediate (30 Days)", "Medium-Term (90 Days)", "Long-Term (1 Year)"]
    initiative: str
    expected_roi: str
    owner: str


class ComprehensiveReportResult(BaseModel):
    title: str
    executive_summary: str
    domain_assessment: str
    key_insights_summary: List[str] = Field(default_factory=list)
    strategic_recommendations: List[StrategicRecommendation] = Field(default_factory=list)
    full_markdown_report: str
    styled_html_report: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==========================================
# Shared Pipeline State & Progress
# ==========================================
class AgentProgress(BaseModel):
    agent_id: str
    agent_name: str
    status: Literal["idle", "waiting", "running", "completed", "error"] = "idle"
    progress_pct: int = 0
    message: str = ""
    duration_seconds: float = 0.0


class AnalysisState(BaseModel):
    dataset_path: str = ""
    dataset_name: str = ""
    total_rows: int = 0
    total_columns: int = 0
    column_names: List[str] = Field(default_factory=list)
    quick_preview: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent Outputs
    dataset_description: Optional[DatasetDescriptionResult] = None
    domain_patterns: Optional[DomainPatternsResult] = None
    visualizations: Optional[VisualizationResult] = None
    custom_analysis: Optional[CustomAnalysisResult] = None
    business_goals: Optional[BusinessGoalsResult] = None
    comprehensive_report: Optional[ComprehensiveReportResult] = None
    
    # Progress & Telemetry
    agent_progress: Dict[str, AgentProgress] = Field(default_factory=dict)
    execution_logs: List[str] = Field(default_factory=list)
