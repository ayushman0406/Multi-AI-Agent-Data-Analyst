#!/usr/bin/env python
# coding: utf-8

"""
Comprehensive Report Generation Agent
Generates final comprehensive reports by combining outputs from all other agents
"""

from phi.agent import Agent
from phi.model.groq import Groq
import os
import logging
import json
import pandas as pd
from datetime import datetime
import glob

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_API_KEY"] = "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"

class ComprehensiveReportAgent:
    def __init__(self, dataset_name="Unknown Dataset"):
        """
        Initialize the comprehensive report generation agent.
        
        Args:
            dataset_name (str): Name of the dataset being analyzed
        """
        self.dataset_name = dataset_name
        
        # Initialize the AI agent
        if Agent and Groq:
            self.agent = Agent(
                name="Comprehensive Report Generation Agent",
                model=Groq(id="llama-3.3-70b-versatile"),
                instructions=[
                    "You are a specialized report generation expert focused on creating comprehensive business reports.",
                    "Combine insights from multiple data analysis agents into a cohesive, actionable report.",
                    "Generate executive summaries, detailed findings, and strategic recommendations.",
                    "Create reports suitable for business stakeholders, data scientists, and decision makers.",
                    "Ensure reports are well-structured, clear, and provide actionable insights."
                ],
                markdown=True,
            )
        else:
            self.agent = None
            print("Warning: AI agent not available. Install phidata library for AI functionality.")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_agent_outputs(self):
        """Load outputs from all other agents."""
        try:
            agent_outputs = {}
            
            # Define expected output files
            output_files = {
                "dataset_description": "dataset_description_output.json",
                "domain_patterns": "domain_patterns_output.json",
                "visualizations": "visualizations_output.json",
                "custom_analysis": "custom_analysis_output.json",
                "business_goals": "business_goals_output.json"
            }
            
            # Load each agent's output
            for agent_name, filename in output_files.items():
                try:
                    if os.path.exists(filename):
                        with open(filename, 'r') as f:
                            agent_outputs[agent_name] = json.load(f)
                        self.logger.info(f"Loaded {agent_name} output from {filename}")
                    else:
                        self.logger.warning(f"Output file {filename} not found for {agent_name}")
                        agent_outputs[agent_name] = {"error": f"Output file {filename} not found"}
                except Exception as e:
                    self.logger.error(f"Error loading {filename}: {e}")
                    agent_outputs[agent_name] = {"error": str(e)}
            
            return agent_outputs
            
        except Exception as e:
            self.logger.error(f"Error loading agent outputs: {e}")
            return {}
    
    def create_agent_summaries(self, agent_outputs):
        """Level 1: Create concise summaries for each agent's output."""
        try:
            summaries = {}
            
            # Dataset Description Agent Summary
            if "dataset_description" in agent_outputs:
                desc_data = agent_outputs["dataset_description"]
                summaries["dataset_description"] = {
                    "overview": f"Dataset contains {desc_data.get('total_records', 'Unknown')} records with {len(desc_data.get('schema_analysis', {}).get('column_names', []))} columns",
                    "quality": f"Data quality: {len(desc_data.get('data_quality', {}).get('issues', []))} issues identified",
                    "business_context": desc_data.get('descriptions', {}).get('business_description', '')[:100] + ("..." if len(desc_data.get('descriptions', {}).get('business_description', '')) > 100 else ""),
                    "technical_context": desc_data.get('descriptions', {}).get('technical_description', '')[:100] + ("..." if len(desc_data.get('descriptions', {}).get('technical_description', '')) > 100 else "")
                }
            
            # Domain Patterns Agent Summary
            if "domain_patterns" in agent_outputs:
                patterns_data = agent_outputs["domain_patterns"]
                domain_insights = patterns_data.get('domain_insights', '')
                business_recommendations = patterns_data.get('business_recommendations', '')
                correlations = patterns_data.get('analysis_data', {}).get('correlations', {})
                temporal_patterns = patterns_data.get('analysis_data', {}).get('temporal_patterns', {})
                
                summaries["domain_patterns"] = {
                    "insights": domain_insights[:150] + ("..." if len(domain_insights) > 150 else ""),
                    "recommendations": business_recommendations[:150] + ("..." if len(business_recommendations) > 150 else ""),
                    "correlations": f"Found {len(correlations)} significant correlations",
                    "temporal": f"Temporal patterns identified in {len(temporal_patterns)} time dimensions"
                }
            
            # Business Goals Agent Summary
            if "business_goals" in agent_outputs:
                goals_data = agent_outputs["business_goals"]
                revenue_analysis = goals_data.get('revenue_analysis', {})
                customer_analysis = goals_data.get('customer_analysis', {})
                business_goals = goals_data.get('business_goals', '')
                
                summaries["business_goals"] = {
                    "revenue": f"Revenue analysis: {revenue_analysis.get('total_revenue', 'Unknown')} total revenue",
                    "customer": f"Customer analysis: {customer_analysis.get('total_customers', 'Unknown')} customers analyzed",
                    "goals": business_goals[:100] + ("..." if len(business_goals) > 100 else ""),
                    "optimization": f"Optimization opportunities: {len(revenue_analysis.get('optimization_opportunities', []))} identified"
                }
            
            # Visualizations Agent Summary
            if "visualizations" in agent_outputs:
                viz_data = agent_outputs["visualizations"]
                visualizations = viz_data.get('visualizations', {})
                additional_recommendations = viz_data.get('additional_recommendations', '')
                
                summaries["visualizations"] = {
                    "count": f"Generated {viz_data.get('visualization_count', 0)} visualizations",
                    "types": f"Types: {', '.join(list(visualizations.keys())[:3])}" + ("..." if len(visualizations) > 3 else ""),
                    "recommendations": additional_recommendations[:100] + ("..." if len(additional_recommendations) > 100 else "")
                }
            
            # Custom Analysis Agent Summary
            if "custom_analysis" in agent_outputs:
                analysis_data = agent_outputs["custom_analysis"]
                analysis_results = analysis_data.get('analysis_results', {})
                statistical_analysis = analysis_results.get('statistical_analysis', {})
                clustering_analysis = analysis_results.get('clustering_analysis', {})
                correlation_analysis = analysis_results.get('correlation_analysis', {})
                
                summaries["custom_analysis"] = {
                    "statistical": f"Statistical analysis: {len(statistical_analysis)} metrics analyzed",
                    "clustering": f"Clustering: {len(clustering_analysis.get('clusters', []))} clusters identified",
                    "correlations": f"Correlation patterns: {len(correlation_analysis)} found",
                    "custom_code": f"Custom analysis: {analysis_data.get('custom_code_executed', False)}"
                }
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"Error creating agent summaries: {e}")
            return {}
    
    def create_section_summaries(self, agent_summaries):
        """Level 2: Create section summaries from agent summaries."""
        try:
            sections = {}
            
            # Data Overview Section
            sections["data_overview"] = {
                "content": f"""
                Dataset Analysis Summary:
                - {agent_summaries.get('dataset_description', {}).get('overview', 'No dataset information available')}
                - {agent_summaries.get('dataset_description', {}).get('quality', 'No quality assessment available')}
                - {agent_summaries.get('visualizations', {}).get('count', 'No visualization information available')}
                - Business Context: {agent_summaries.get('dataset_description', {}).get('business_context', 'Not available')}
                """,
                "key_metrics": [
                    agent_summaries.get('dataset_description', {}).get('overview', ''),
                    agent_summaries.get('dataset_description', {}).get('quality', ''),
                    agent_summaries.get('visualizations', {}).get('count', '')
                ]
            }
            
            # Business Insights Section
            sections["business_insights"] = {
                "content": f"""
                Business Intelligence Summary:
                - Domain Insights: {agent_summaries.get('domain_patterns', {}).get('insights', 'No domain insights available')}
                - Business Recommendations: {agent_summaries.get('domain_patterns', {}).get('recommendations', 'No recommendations available')}
                - Revenue Analysis: {agent_summaries.get('business_goals', {}).get('revenue', 'No revenue information available')}
                - Customer Analysis: {agent_summaries.get('business_goals', {}).get('customer', 'No customer information available')}
                - Business Goals: {agent_summaries.get('business_goals', {}).get('goals', 'No business goals available')}
                """,
                "key_metrics": [
                    agent_summaries.get('domain_patterns', {}).get('insights', ''),
                    agent_summaries.get('business_goals', {}).get('revenue', ''),
                    agent_summaries.get('business_goals', {}).get('goals', '')
                ]
            }
            
            # Technical Analysis Section
            sections["technical_analysis"] = {
                "content": f"""
                Technical Analysis Summary:
                - Statistical Analysis: {agent_summaries.get('custom_analysis', {}).get('statistical', 'No statistical analysis available')}
                - Clustering Analysis: {agent_summaries.get('custom_analysis', {}).get('clustering', 'No clustering analysis available')}
                - Correlation Analysis: {agent_summaries.get('custom_analysis', {}).get('correlations', 'No correlation analysis available')}
                - Domain Correlations: {agent_summaries.get('domain_patterns', {}).get('correlations', 'No correlation information available')}
                - Temporal Patterns: {agent_summaries.get('domain_patterns', {}).get('temporal', 'No temporal analysis available')}
                """,
                "key_metrics": [
                    agent_summaries.get('custom_analysis', {}).get('statistical', ''),
                    agent_summaries.get('custom_analysis', {}).get('clustering', ''),
                    agent_summaries.get('domain_patterns', {}).get('correlations', '')
                ]
            }
            
            # Visualization and Recommendations Section
            sections["visualizations_recommendations"] = {
                "content": f"""
                Visualization and Recommendations Summary:
                - Visualizations: {agent_summaries.get('visualizations', {}).get('count', 'No visualization information available')}
                - Visualization Types: {agent_summaries.get('visualizations', {}).get('types', 'No type information available')}
                - Additional Recommendations: {agent_summaries.get('visualizations', {}).get('recommendations', 'No additional recommendations available')}
                - Optimization Opportunities: {agent_summaries.get('business_goals', {}).get('optimization', 'No optimization opportunities identified')}
                """,
                "key_metrics": [
                    agent_summaries.get('visualizations', {}).get('count', ''),
                    agent_summaries.get('business_goals', {}).get('optimization', '')
                ]
            }
            
            return sections
            
        except Exception as e:
            self.logger.error(f"Error creating section summaries: {e}")
            return {}
    
    def generate_executive_summary(self, section_summaries):
        """Level 3: Generate executive summary from section summaries."""
        try:
            summary_prompt = f"""
            Generate an executive summary for a comprehensive data analysis report based on the following section summaries:
            
            Data Overview:
            {section_summaries.get('data_overview', {}).get('content', 'No data overview available')}
            
            Business Insights:
            {section_summaries.get('business_insights', {}).get('content', 'No business insights available')}
            
            Technical Analysis:
            {section_summaries.get('technical_analysis', {}).get('content', 'No technical analysis available')}
            
            Visualizations and Recommendations:
            {section_summaries.get('visualizations_recommendations', {}).get('content', 'No visualization information available')}
            
            Please provide:
            
            1. EXECUTIVE SUMMARY (2-3 paragraphs):
               - High-level overview of the dataset and analysis
               - Key findings and business implications
               - Strategic recommendations for leadership
            
            2. KEY PERFORMANCE INDICATORS:
               - Important metrics identified from the data
               - Current performance benchmarks
               - Target improvements
            
            3. STRATEGIC RECOMMENDATIONS:
               - Top 3-5 actionable recommendations
               - Expected business impact
               - Implementation priorities
            """
            
            if self.agent:
                self.logger.info("Generating executive summary...")
                self.agent.print_response(summary_prompt, stream=True)
            
            return "Executive summary generated by the agent"
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {e}")
            return "Error generating executive summary"
    
    def generate_detailed_findings(self, section_summaries):
        """Generate detailed findings section from section summaries."""
        try:
            findings_prompt = f"""
            Generate detailed findings for a comprehensive data analysis report based on the following section summaries:
            
            Data Overview:
            {section_summaries.get('data_overview', {}).get('content', 'No data overview available')}
            
            Business Insights:
            {section_summaries.get('business_insights', {}).get('content', 'No business insights available')}
            
            Technical Analysis:
            {section_summaries.get('technical_analysis', {}).get('content', 'No technical analysis available')}
            
            Visualizations and Recommendations:
            {section_summaries.get('visualizations_recommendations', {}).get('content', 'No visualization information available')}
            
            Please provide:
            
            1. DATA QUALITY FINDINGS:
               - Data completeness and accuracy
               - Data quality issues identified
               - Recommendations for data improvement
            
            2. BUSINESS INTELLIGENCE FINDINGS:
               - Key patterns and trends discovered
               - Customer behavior insights
               - Revenue and performance insights
            
            3. TECHNICAL ANALYSIS FINDINGS:
               - Statistical analysis results
               - Machine learning insights
               - Advanced analytics findings
            
            4. VISUALIZATION INSIGHTS:
               - Key visualizations created
               - Insights derived from visualizations
               - Additional visualization recommendations
            """
            
            if self.agent:
                self.logger.info("Generating detailed findings...")
                self.agent.print_response(findings_prompt, stream=True)
            
            return "Detailed findings generated by the agent"
            
        except Exception as e:
            self.logger.error(f"Error generating detailed findings: {e}")
            return "Error generating detailed findings"
    
    def generate_strategic_recommendations(self, section_summaries):
        """Generate strategic recommendations section from section summaries."""
        try:
            recommendations_prompt = f"""
            Generate strategic recommendations for a comprehensive data analysis report based on the following section summaries:
            
            Business Insights:
            {section_summaries.get('business_insights', {}).get('content', 'No business insights available')}
            
            Technical Analysis:
            {section_summaries.get('technical_analysis', {}).get('content', 'No technical analysis available')}
            
            Visualizations and Recommendations:
            {section_summaries.get('visualizations_recommendations', {}).get('content', 'No visualization information available')}
            
            Please provide:
            
            1. IMMEDIATE ACTIONS (Next 30 days):
               - Quick wins and immediate improvements
               - Data quality fixes
               - Process optimizations
            
            2. SHORT-TERM GOALS (Next 3 months):
               - Revenue optimization strategies
               - Customer acquisition improvements
               - Operational efficiency gains
            
            3. LONG-TERM STRATEGY (Next 6-12 months):
               - Strategic business initiatives
               - Technology investments
               - Market expansion opportunities
            
            4. RISK MITIGATION:
               - Identified risks and mitigation strategies
               - Data security and compliance recommendations
               - Business continuity planning
            
            5. SUCCESS METRICS:
               - KPIs to track progress
               - Measurement frameworks
               - Reporting and monitoring recommendations
            """
            
            if self.agent:
                self.logger.info("Generating strategic recommendations...")
                self.agent.print_response(recommendations_prompt, stream=True)
            
            return "Strategic recommendations generated by the agent"
            
        except Exception as e:
            self.logger.error(f"Error generating strategic recommendations: {e}")
            return "Error generating strategic recommendations"
    
    def generate_comprehensive_report(self):
        """
        Generate a comprehensive report using hierarchical summarization approach.
        Returns:
            dict: A dictionary containing the comprehensive report in similar format to local_data_analysis_agent.
        """
        try:
            # Load outputs from all agents
            agent_outputs = self.load_agent_outputs()
            
            # Level 1: Create agent summaries
            agent_summaries = self.create_agent_summaries(agent_outputs)
            
            # Level 2: Create section summaries
            section_summaries = self.create_section_summaries(agent_summaries)
            
            # Level 3: Generate report sections using hierarchical approach
            executive_summary = self.generate_executive_summary(section_summaries)
            detailed_findings = self.generate_detailed_findings(section_summaries)
            strategic_recommendations = self.generate_strategic_recommendations(section_summaries)
            
            # Extract key data from agent outputs for the final report structure
            dataset_description = agent_outputs.get("dataset_description", {})
            domain_patterns = agent_outputs.get("domain_patterns", {})
            business_goals = agent_outputs.get("business_goals", {})
            visualizations = agent_outputs.get("visualizations", {})
            custom_analysis = agent_outputs.get("custom_analysis", {})
            
            # Compile comprehensive report in similar format to local_data_analysis_agent
            report = {
                    "dataset_name": self.dataset_name,
                "business_description": dataset_description.get("descriptions", {}).get("business_description", "Business description not available"),
                "technical_description": dataset_description.get("descriptions", {}).get("technical_description", "Technical description not available"),
                "data_quality": {
                    "total_records": dataset_description.get("total_records", "Unknown"),
                    "null_counts": dataset_description.get("data_quality", {}).get("null_counts", {}),
                    "duplicate_records": dataset_description.get("data_quality", {}).get("duplicate_records", "Unknown"),
                    "data_quality_issues": dataset_description.get("data_quality", {}).get("issues", []),
                    "schema_analysis": dataset_description.get("schema_analysis", {})
                },
                "domain_insights": {
                    "domain_insights": domain_patterns.get("domain_insights", "No domain insights available"),
                    "business_recommendations": domain_patterns.get("business_recommendations", "No business recommendations available"),
                    "correlations": domain_patterns.get("analysis_data", {}).get("correlations", {}),
                    "temporal_patterns": domain_patterns.get("analysis_data", {}).get("temporal_patterns", {}),
                    "category_distributions": domain_patterns.get("analysis_data", {}).get("category_distributions", {})
                },
                "business_goals": {
                    "revenue_analysis": business_goals.get("revenue_analysis", {}),
                    "customer_analysis": business_goals.get("customer_analysis", {}),
                    "business_goals": business_goals.get("business_goals", "No business goals defined"),
                    "optimization_opportunities": business_goals.get("revenue_analysis", {}).get("optimization_opportunities", [])
                },
                "visualizations": {
                    "visualization_count": visualizations.get("visualization_count", 0),
                    "visualization_types": list(visualizations.get("visualizations", {}).keys()),
                    "visualization_descriptions": visualizations.get("visualization_descriptions", {}),
                    "additional_recommendations": visualizations.get("additional_recommendations", "No additional recommendations")
                },
                "technical_analysis": {
                    "statistical_analysis": custom_analysis.get("analysis_results", {}).get("statistical_analysis", {}),
                    "clustering_analysis": custom_analysis.get("analysis_results", {}).get("clustering_analysis", {}),
                    "correlation_analysis": custom_analysis.get("analysis_results", {}).get("correlation_analysis", {}),
                    "custom_code_executed": custom_analysis.get("custom_code_executed", False)
                },
                "executive_summary": executive_summary,
                "detailed_findings": detailed_findings,
                "strategic_recommendations": strategic_recommendations,
                "recommendations": "Comprehensive recommendations generated by multi-agent analysis system",
                "next_steps": [
                    "Review and implement strategic recommendations",
                    "Address identified data quality issues",
                    "Execute optimization opportunities",
                    "Monitor key performance indicators",
                    "Schedule follow-up analysis"
                ],
                "report_metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "report_version": "2.0",
                    "method": "hierarchical_summarization",
                    "agents_used": list(agent_outputs.keys()),
                    "total_agents_processed": len(agent_outputs),
                    "context_optimization": "Hierarchical summarization used to reduce context length",
                    "hierarchical_levels": {
                        "level_0": "Raw agent outputs (JSON files)",
                        "level_1": "Agent summaries (concise insights)",
                        "level_2": "Section summaries (grouped insights)",
                        "level_3": "Executive summary (final report)"
                    }
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            raise
    
    def save_report(self, output_path="comprehensive_report.json"):
        """Save the comprehensive report to a JSON file."""
        try:
            report = self.generate_comprehensive_report()
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Comprehensive report saved to {output_path}")
            return report
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            raise
    
    def generate_markdown_report(self, output_path="comprehensive_report.md"):
        """Generate a markdown version of the report using the new structure similar to local_data_analysis_agent."""
        try:
            report = self.generate_comprehensive_report()
            
            markdown_content = f"""# Comprehensive Data Analysis Report

## Report Metadata
- **Dataset**: {report['dataset_name']}
- **Generated**: {report['report_metadata']['generation_timestamp']}
- **Version**: {report['report_metadata']['report_version']}
- **Method**: {report['report_metadata']['method']}
- **Agents Used**: {', '.join(report['report_metadata']['agents_used'])}

## Executive Summary
{report['executive_summary']}

## Dataset Overview

### Business Description
{report['business_description']}

### Technical Description
{report['technical_description']}

## Data Quality Assessment
- **Total Records**: {report['data_quality']['total_records']}
- **Duplicate Records**: {report['data_quality']['duplicate_records']}
- **Data Quality Issues**: {len(report['data_quality']['data_quality_issues'])} issues identified
- **Null Counts by Column**: {report['data_quality']['null_counts']}

## Key Insights

### Domain Insights
{report['domain_insights']['domain_insights']}

### Business Recommendations
{report['domain_insights']['business_recommendations']}

### Correlations Found
{len(report['domain_insights']['correlations'])} correlation patterns identified

### Temporal Patterns
{len(report['domain_insights']['temporal_patterns'])} temporal patterns analyzed

## Business Goals and Revenue Analysis

### Revenue Analysis
{report['business_goals']['revenue_analysis']}

### Customer Analysis
{report['business_goals']['customer_analysis']}

### Business Goals
{report['business_goals']['business_goals']}

### Optimization Opportunities
{len(report['business_goals']['optimization_opportunities'])} opportunities identified

## Visualizations

### Visualization Summary
- **Count**: {report['visualizations']['visualization_count']} visualizations generated
- **Types**: {', '.join(report['visualizations']['visualization_types'])}
- **Additional Recommendations**: {report['visualizations']['additional_recommendations']}

## Technical Analysis

### Statistical Analysis
{len(report['technical_analysis']['statistical_analysis'])} statistical metrics analyzed

### Clustering Analysis
{len(report['technical_analysis']['clustering_analysis'])} clustering patterns identified

### Correlation Analysis
{len(report['technical_analysis']['correlation_analysis'])} correlation analyses performed

### Custom Code Execution
Custom analysis code executed: {report['technical_analysis']['custom_code_executed']}

## Detailed Findings
{report['detailed_findings']}

## Strategic Recommendations
{report['strategic_recommendations']}

## Recommendations
{report['recommendations']}

## Next Steps
{chr(10).join([f"- {step}" for step in report['next_steps']])}

## Report Metadata
- **Generation Timestamp**: {report['report_metadata']['generation_timestamp']}
- **Report Version**: {report['report_metadata']['report_version']}
- **Method**: {report['report_metadata']['method']}
- **Total Agents Processed**: {report['report_metadata']['total_agents_processed']}
- **Context Optimization**: {report['report_metadata']['context_optimization']}

### Hierarchical Structure
{chr(10).join([f"- **{level}**: {description}" for level, description in report['report_metadata']['hierarchical_levels'].items()])}

---
*Report generated by Multi-Agent Data Analysis System with Hierarchical Summarization*
"""
            
            with open(output_path, 'w') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Markdown report saved to {output_path}")
            return markdown_content
            
        except Exception as e:
            self.logger.error(f"Error generating markdown report: {e}")
            raise
    
    def demonstrate_context_reduction(self):
        """Demonstrate the context reduction achieved by hierarchical summarization."""
        try:
            # Load raw agent outputs
            agent_outputs = self.load_agent_outputs()
            
            # Calculate raw data size
            raw_data_size = 0
            for agent_name, output in agent_outputs.items():
                raw_data_size += len(json.dumps(output, default=str))
            
            # Create hierarchical summaries
            agent_summaries = self.create_agent_summaries(agent_outputs)
            section_summaries = self.create_section_summaries(agent_summaries)
            
            # Calculate summary sizes
            agent_summaries_size = len(json.dumps(agent_summaries, default=str))
            section_summaries_size = len(json.dumps(section_summaries, default=str))
            
            # Calculate reduction percentages
            agent_reduction = ((raw_data_size - agent_summaries_size) / raw_data_size) * 100 if raw_data_size > 0 else 0
            section_reduction = ((raw_data_size - section_summaries_size) / raw_data_size) * 100 if raw_data_size > 0 else 0
            
            print("=" * 60)
            print("HIERARCHICAL SUMMARIZATION - CONTEXT REDUCTION DEMO")
            print("=" * 60)
            print(f"Raw Agent Outputs Size: {raw_data_size:,} characters")
            print(f"Agent Summaries Size: {agent_summaries_size:,} characters")
            print(f"Section Summaries Size: {section_summaries_size:,} characters")
            print("-" * 60)
            print(f"Agent Summaries Reduction: {agent_reduction:.1f}%")
            print(f"Section Summaries Reduction: {section_reduction:.1f}%")
            print("-" * 60)
            print(f"Context Usage: {'WITHIN LIMITS' if section_summaries_size < 4000 else 'EXCEEDS LIMITS'}")
            print("=" * 60)
            
            return {
                "raw_data_size": raw_data_size,
                "agent_summaries_size": agent_summaries_size,
                "section_summaries_size": section_summaries_size,
                "agent_reduction_percent": agent_reduction,
                "section_reduction_percent": section_reduction
            }
            
        except Exception as e:
            self.logger.error(f"Error demonstrating context reduction: {e}")
            return None

    def cleanup(self):
        """
        Clean up resources used by the comprehensive report agent.
        This method is required for compatibility with the Streamlit app.
        """
        try:
            # Since this agent doesn't use Spark or other resources that need cleanup,
            # we just log the cleanup action
            self.logger.info("Comprehensive Report Agent cleanup completed")
            
            # If there were any temporary files or resources to clean up,
            # they would be handled here
            # For now, this is a placeholder for future cleanup needs
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Don't raise the exception during cleanup to avoid masking other errors

    def generate_final_report_display(self):
        """
        Generate a clean, formatted final report for display in Streamlit.
        Returns a formatted string similar to the example provided.
        """
        try:
            # Generate the comprehensive report
            report = self.generate_comprehensive_report()
            
            # Format the report for clean display
            formatted_report = f"""
┏━ Comprehensive Report ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                                            ┃
┃                                    Executive Summary                                       ┃
┃                                                                                            ┃
{self._format_text_block(report.get('executive_summary', 'No executive summary available'))}
┃                                                                                            ┃
┃                                    Dataset Overview                                        ┃
┃                                                                                            ┃
┃                                   Business Description                                     ┃
┃                                                                                            ┃
{self._format_text_block(report.get('business_description', 'No business description available'))}
┃                                                                                            ┃
┃                                   Technical Description                                    ┃
┃                                                                                            ┃
{self._format_text_block(report.get('technical_description', 'No technical description available'))}
┃                                                                                            ┃
┃                                  Data Quality Assessment                                   ┃
┃                                                                                            ┃
{self._format_data_quality(report.get('data_quality', {}))}
┃                                                                                            ┃
┃                                       Key Insights                                        ┃
┃                                                                                            ┃
{self._format_domain_insights(report.get('domain_insights', {}))}
┃                                                                                            ┃
┃                                  Business Goals & Revenue                                  ┃
┃                                                                                            ┃
{self._format_business_goals(report.get('business_goals', {}))}
┃                                                                                            ┃
┃                                      Visualizations                                       ┃
┃                                                                                            ┃
{self._format_visualizations(report.get('visualizations', {}))}
┃                                                                                            ┃
┃                                   Technical Analysis                                      ┃
┃                                                                                            ┃
{self._format_technical_analysis(report.get('technical_analysis', {}))}
┃                                                                                            ┃
┃                                  Strategic Recommendations                                 ┃
┃                                                                                            ┃
{self._format_text_block(report.get('strategic_recommendations', 'No strategic recommendations available'))}
┃                                                                                            ┃
┃                                       Next Steps                                          ┃
┃                                                                                            ┃
{self._format_next_steps(report.get('next_steps', []))}
┃                                                                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
            
            return formatted_report
            
        except Exception as e:
            self.logger.error(f"Error generating final report display: {e}")
            return f"Error generating report: {e}"

    def _format_text_block(self, text, max_width=80):
        """Format text to fit within the display width."""
        if not text:
            return "┃ No information available" + " " * (max_width - 25) + "┃"
        
        # Clean up the text and wrap it
        clean_text = str(text).strip()
        if len(clean_text) <= max_width - 4:
            return f"┃ {clean_text}" + " " * (max_width - len(clean_text) - 3) + "┃"
        
        # Wrap long text
        lines = []
        words = clean_text.split()
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_width - 4:
                current_line += (" " + word) if current_line else word
            else:
                if current_line:
                    lines.append(f"┃ {current_line}" + " " * (max_width - len(current_line) - 3) + "┃")
                current_line = word
        
        if current_line:
            lines.append(f"┃ {current_line}" + " " * (max_width - len(current_line) - 3) + "┃")
        
        return "\n".join(lines) if lines else "┃ No information available" + " " * (max_width - 25) + "┃"

    def _format_data_quality(self, data_quality):
        """Format data quality information."""
        if not data_quality:
            return "┃ No data quality information available" + " " * 42 + "┃"
        
        lines = []
        lines.append(f"┃ • Total Records: {data_quality.get('total_records', 'Unknown')}" + " " * (80 - 30 - len(str(data_quality.get('total_records', 'Unknown')))) + "┃")
        lines.append(f"┃ • Duplicate Records: {data_quality.get('duplicate_records', 'Unknown')}" + " " * (80 - 35 - len(str(data_quality.get('duplicate_records', 'Unknown')))) + "┃")
        
        # Add null counts if available
        null_counts = data_quality.get('null_counts', {})
        if null_counts:
            lines.append("┃ • Null Values:" + " " * 66 + "┃")
            for col, count in list(null_counts.items())[:5]:  # Show first 5 columns
                lines.append(f"┃     • {col}: {count}" + " " * (80 - 10 - len(col) - len(str(count))) + "┃")
            if len(null_counts) > 5:
                lines.append(f"┃     • ... and {len(null_counts) - 5} more columns" + " " * (80 - 35 - len(str(len(null_counts) - 5))) + "┃")
        
        return "\n".join(lines)

    def _format_domain_insights(self, domain_insights):
        """Format domain insights information."""
        if not domain_insights:
            return "┃ No domain insights available" + " " * 50 + "┃"
        
        lines = []
        insights = domain_insights.get('domain_insights', '')
        if insights:
            lines.append("┃ Domain Insights:" + " " * 62 + "┃")
            lines.append(self._format_text_block(insights))
        
        recommendations = domain_insights.get('business_recommendations', '')
        if recommendations:
            lines.append("┃ Business Recommendations:" + " " * 52 + "┃")
            lines.append(self._format_text_block(recommendations))
        
        return "\n".join(lines) if lines else "┃ No domain insights available" + " " * 50 + "┃"

    def _format_business_goals(self, business_goals):
        """Format business goals information."""
        if not business_goals:
            return "┃ No business goals information available" + " " * 42 + "┃"
        
        lines = []
        goals = business_goals.get('business_goals', '')
        if goals:
            lines.append("┃ Business Goals:" + " " * 63 + "┃")
            lines.append(self._format_text_block(goals))
        
        revenue_analysis = business_goals.get('revenue_analysis', {})
        if revenue_analysis:
            lines.append("┃ Revenue Analysis:" + " " * 61 + "┃")
            for key, value in list(revenue_analysis.items())[:3]:  # Show first 3 items
                lines.append(f"┃ • {key}: {value}" + " " * (80 - 6 - len(str(key)) - len(str(value))) + "┃")
        
        return "\n".join(lines) if lines else "┃ No business goals information available" + " " * 42 + "┃"

    def _format_visualizations(self, visualizations):
        """Format visualizations information."""
        if not visualizations:
            return "┃ No visualization information available" + " " * 42 + "┃"
        
        lines = []
        count = visualizations.get('visualization_count', 0)
        lines.append(f"┃ • Total Visualizations: {count}" + " " * (80 - 30 - len(str(count))) + "┃")
        
        types = visualizations.get('visualization_types', [])
        if types:
            types_str = ", ".join(types[:3])  # Show first 3 types
            if len(types) > 3:
                types_str += f" ... and {len(types) - 3} more"
            lines.append(f"┃ • Types: {types_str}" + " " * (80 - 10 - len(types_str)) + "┃")
        
        recommendations = visualizations.get('additional_recommendations', '')
        if recommendations:
            lines.append("┃ • Recommendations:" + " " * 60 + "┃")
            lines.append(self._format_text_block(recommendations))
        
        return "\n".join(lines) if lines else "┃ No visualization information available" + " " * 42 + "┃"

    def _format_technical_analysis(self, technical_analysis):
        """Format technical analysis information."""
        if not technical_analysis:
            return "┃ No technical analysis available" + " " * 48 + "┃"
        
        lines = []
        stats = technical_analysis.get('statistical_analysis', {})
        if stats:
            lines.append(f"┃ • Statistical Analysis: {len(stats)} metrics analyzed" + " " * (80 - 45 - len(str(len(stats)))) + "┃")
        
        clustering = technical_analysis.get('clustering_analysis', {})
        if clustering:
            lines.append(f"┃ • Clustering Analysis: {len(clustering)} patterns identified" + " " * (80 - 45 - len(str(len(clustering)))) + "┃")
        
        correlations = technical_analysis.get('correlation_analysis', {})
        if correlations:
            lines.append(f"┃ • Correlation Analysis: {len(correlations)} correlations found" + " " * (80 - 45 - len(str(len(correlations)))) + "┃")
        
        return "\n".join(lines) if lines else "┃ No technical analysis available" + " " * 48 + "┃"

    def _format_next_steps(self, next_steps):
        """Format next steps information."""
        if not next_steps:
            return "┃ No next steps defined" + " " * 58 + "┃"
        
        lines = []
        for i, step in enumerate(next_steps[:5], 1):  # Show first 5 steps
            lines.append(f"┃ {i}. {step}" + " " * (80 - 4 - len(str(i)) - len(step)) + "┃")
        
        if len(next_steps) > 5:
            lines.append(f"┃ ... and {len(next_steps) - 5} more steps" + " " * (80 - 25 - len(str(len(next_steps) - 5))) + "┃")
        
        return "\n".join(lines) if lines else "┃ No next steps defined" + " " * 58 + "┃"

# Usage
if __name__ == "__main__":
    # Initialize the agent
    agent = ComprehensiveReportAgent("green_taxi_data.csv")
    
    try:
        print("=" * 80)
        print("HIERARCHICAL SUMMARIZATION APPROACH - COMPREHENSIVE REPORT GENERATION")
        print("=" * 80)
        
        # Demonstrate context reduction
        print("\n1. DEMONSTRATING CONTEXT REDUCTION:")
        context_stats = agent.demonstrate_context_reduction()
        
        print("\n2. GENERATING COMPREHENSIVE REPORT:")
        # Generate comprehensive report using hierarchical approach
        report = agent.save_report("comprehensive_report.json")
        
        # Generate markdown report
        agent.generate_markdown_report("comprehensive_report.md")
        
        # Display the final report in clean format
        print("\n3. FINAL REPORT DISPLAY:")
        print("=" * 80)
        final_report = agent.generate_final_report_display()
        print(final_report)
        
        print("\n4. REPORT GENERATION COMPLETED SUCCESSFULLY!")
        print(f"   - Report includes insights from {len(report['report_metadata']['agents_used'])} agents")
        print(f"   - Dataset: {report['dataset_name']}")
        print(f"   - Method: {report['report_metadata']['method']}")
        print(f"   - Version: {report['report_metadata']['report_version']}")
        print(f"   - Total Records: {report['data_quality']['total_records']}")
        print(f"   - Visualizations Generated: {report['visualizations']['visualization_count']}")
        print(f"   - Optimization Opportunities: {len(report['business_goals']['optimization_opportunities'])}")
        
        print("\n5. OUTPUT FILES GENERATED:")
        print("   - comprehensive_report.json (structured data)")
        print("   - comprehensive_report.md (human-readable)")
        
        print("\n6. HIERARCHICAL STRUCTURE:")
        for level, description in report['report_metadata']['hierarchical_levels'].items():
            print(f"   - {level}: {description}")
        
        print("\n7. REPORT SECTIONS:")
        print("   - Executive Summary")
        print("   - Dataset Overview (Business & Technical)")
        print("   - Data Quality Assessment")
        print("   - Key Insights (Domain & Business)")
        print("   - Business Goals & Revenue Analysis")
        print("   - Visualizations")
        print("   - Technical Analysis")
        print("   - Strategic Recommendations")
        print("   - Next Steps")
        
        print("\n" + "=" * 80)
        print("CONTEXT LENGTH ISSUE RESOLVED WITH HIERARCHICAL SUMMARIZATION!")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error during report generation: {e}")
        import traceback
        traceback.print_exc()
