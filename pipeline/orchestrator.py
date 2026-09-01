"""
Pipeline Orchestrator
Coordinates execution of all 6 agents in a structured DAG with shared AnalysisState,
real-time telemetry callbacks for SSE streaming, and conversational Q&A capability.
"""

import time
import json
import logging
from typing import Optional, Callable, Dict, Any
from engine.data_engine import DataEngine
from llm.llm_gateway import LLMGateway
from models.schemas import AnalysisState, AgentProgress
from generate_dataset_description_agent import DatasetDescriptionAgent
from analyze_domain_specific_patterns_agent import DomainSpecificPatternsAgent
from generate_visualizations_agent import VisualizationsAgent
from execute_custom_analysis_agent import CustomAnalysisAgent
from define_business_goals_agent import BusinessGoalsAgent
from generate_comprehensive_report_agent import ComprehensiveReportAgent

logger = logging.getLogger(__name__)

AGENT_STAGES = [
    {"id": "profiler", "name": "Dataset Description Agent", "step": 1},
    {"id": "patterns", "name": "Domain Patterns Agent", "step": 2},
    {"id": "visualizations", "name": "Visualizations Agent", "step": 3},
    {"id": "custom_analysis", "name": "Custom Analysis Agent", "step": 4},
    {"id": "business_goals", "name": "Business Goals Agent", "step": 5},
    {"id": "report", "name": "Comprehensive Report Agent", "step": 6},
]


class AnalysisPipeline:
    def __init__(
        self,
        data_source: str,
        limit: Optional[int] = 1000,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.data_source = data_source
        self.limit = limit
        self.engine = DataEngine(data_source, limit=limit)
        self.llm = LLMGateway(provider=provider, model=model, api_key=api_key)
        
        # Initialize state
        self.state = AnalysisState(
            dataset_path=data_source,
            dataset_name=self.engine.dataset_name,
            total_rows=self.engine.total_rows,
            total_columns=self.engine.total_columns,
            column_names=self.engine.column_names,
            quick_preview=self.engine.get_sample_rows(n=5),
            agent_progress={
                stage["id"]: AgentProgress(
                    agent_id=stage["id"],
                    agent_name=stage["name"],
                    status="waiting",
                    progress_pct=0,
                    message="Pending execution"
                )
                for stage in AGENT_STAGES
            }
        )

    def _emit(self, callback: Optional[Callable[[Dict[str, Any]], None]], event_type: str, data: Dict[str, Any]):
        """Helper to emit events to callback if provided."""
        if callback:
            try:
                callback({"type": event_type, "timestamp": time.time(), **data})
            except Exception as e:
                logger.warning(f"Error in progress callback: {e}")

    def run_full_pipeline(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> AnalysisState:
        """
        Executes the full 6-agent DAG synchronously, calling progress_callback at each step.
        """
        logger.info(f"Starting end-to-end multi-agent pipeline for {self.engine.dataset_name}...")
        self._emit(progress_callback, "pipeline_start", {"dataset": self.engine.dataset_name, "total_steps": 6})

        total_stages = len(AGENT_STAGES)
        
        for idx, stage in enumerate(AGENT_STAGES):
            agent_id = stage["id"]
            agent_name = stage["name"]
            overall_pct = int(((idx) / total_stages) * 100)
            
            # Mark running
            start_time = time.time()
            self.state.agent_progress[agent_id].status = "running"
            self.state.agent_progress[agent_id].message = f"Executing {agent_name}..."
            self.state.agent_progress[agent_id].progress_pct = overall_pct
            self._emit(progress_callback, "agent_started", {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "step": idx + 1,
                "overall_pct": overall_pct
            })

            try:
                if agent_id == "profiler":
                    agent1 = DatasetDescriptionAgent(self.data_source, data_engine=self.engine, llm_gateway=self.llm)
                    self.state.dataset_description = agent1.generate_dataset_description()
                    
                elif agent_id == "patterns":
                    agent2 = DomainSpecificPatternsAgent(self.data_source, data_engine=self.engine, llm_gateway=self.llm)
                    self.state.domain_patterns = agent2.analyze_domain_patterns(self.state.dataset_description)
                    
                elif agent_id == "visualizations":
                    agent3 = VisualizationsAgent(self.data_source, data_engine=self.engine, llm_gateway=self.llm)
                    self.state.visualizations = agent3.generate_visualizations()
                    
                elif agent_id == "custom_analysis":
                    agent4 = CustomAnalysisAgent(self.data_source, data_engine=self.engine, llm_gateway=self.llm)
                    self.state.custom_analysis = agent4.execute_custom_analysis()
                    
                elif agent_id == "business_goals":
                    agent5 = BusinessGoalsAgent(self.data_source, data_engine=self.engine, llm_gateway=self.llm)
                    self.state.business_goals = agent5.define_business_goals(
                        dataset_description=self.state.dataset_description,
                        domain_patterns=self.state.domain_patterns
                    )
                    
                elif agent_id == "report":
                    agent6 = ComprehensiveReportAgent(dataset_name=self.engine.dataset_name, llm_gateway=self.llm)
                    self.state.comprehensive_report = agent6.generate_comprehensive_report(state=self.state)

                elapsed = round(time.time() - start_time, 2)
                end_pct = int(((idx + 1) / total_stages) * 100)
                self.state.agent_progress[agent_id].status = "completed"
                self.state.agent_progress[agent_id].progress_pct = end_pct
                self.state.agent_progress[agent_id].duration_seconds = elapsed
                self.state.agent_progress[agent_id].message = f"Completed in {elapsed}s"
                
                self._emit(progress_callback, "agent_completed", {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "step": idx + 1,
                    "duration_seconds": elapsed,
                    "overall_pct": end_pct
                })

            except Exception as e:
                logger.error(f"Agent {agent_id} failed: {e}", exc_info=True)
                elapsed = round(time.time() - start_time, 2)
                self.state.agent_progress[agent_id].status = "error"
                self.state.agent_progress[agent_id].message = f"Error: {str(e)}"
                self.state.agent_progress[agent_id].duration_seconds = elapsed
                self._emit(progress_callback, "agent_error", {
                    "agent_id": agent_id,
                    "error": str(e)
                })

        self._emit(progress_callback, "pipeline_finished", {"state": self.state.model_dump()})
        return self.state

    def chat_with_data(self, user_question: str) -> str:
        """
        Conversational assistant grounded in the entire AnalysisState and dataset schema.
        """
        domain = self.state.dataset_description.business_domain if self.state.dataset_description else "General"
        entities = self.state.dataset_description.key_entities if self.state.dataset_description else []
        recs = [r.initiative for r in self.state.comprehensive_report.strategic_recommendations] if self.state.comprehensive_report else []
        
        system_prompt = (
            "You are an Elite AI Data Analyst team member. "
            "You have deep knowledge of the uploaded dataset and all 6 analytical agent findings. "
            "Provide concise, mathematically and commercially grounded answers to the user's questions. "
            "Cite specific numbers, feature names, or correlations when relevant."
        )

        context_prompt = f"""
Dataset: {self.state.dataset_name} ({self.state.total_rows:,} rows, {self.state.total_columns} columns)
Domain: {domain}
Key Entities: {entities}
Columns: {self.state.column_names[:25]}

Summary of Strategic Recommendations:
{json.dumps(recs, indent=2)}

User Question:
{user_question}
"""
        return self.llm.generate_text(prompt=context_prompt, system_prompt=system_prompt)
