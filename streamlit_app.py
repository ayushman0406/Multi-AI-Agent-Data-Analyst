#!/usr/bin/env python
# coding: utf-8

"""
Multi-Agent Data Analysis Streamlit App
End-to-end interface for running all 6 specialized data analysis agents
"""

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import json
import os
import sys
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import base64
from contextlib import redirect_stdout
import io
from output_capture import CleanOutputCapture, format_agent_output_for_streamlit

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def cleanup_temp_files():
    """Clean up temporary files created during analysis."""
    try:
        temp_files = [f for f in os.listdir('.') if f.startswith('temp_') and f.endswith('.csv')]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    except Exception as e:
        pass  # Ignore cleanup errors

def check_api_keys():
    """Check if required API keys are available."""
    required_keys = ['GROQ_API_KEY', 'PHI_API_KEY', 'OPENAI_API_KEY']
    available_keys = [key for key in required_keys if os.getenv(key)]
    return len(available_keys) > 0

# Import all agents
try:
    from generate_dataset_description_agent import DatasetDescriptionAgent
    from analyze_domain_specific_patterns_agent import DomainSpecificPatternsAgent
    from generate_visualizations_agent import VisualizationsAgent
    from execute_custom_analysis_agent import CustomAnalysisAgent
    from define_business_goals_agent import BusinessGoalsAgent
    from generate_comprehensive_report_agent import ComprehensiveReportAgent
    from agent_wrapper import get_fallback_analysis, check_dependencies
    AGENTS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Error importing agents: {e}")
    AGENTS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Data Analysis System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application."""
    
    # Check if agents are available
    if not AGENTS_AVAILABLE:
        st.error("❌ **Agents Not Available**")
        st.info("Please make sure all agent files are present and dependencies are installed.")
        st.code("pip install -r streamlit_requirements.txt")
        return
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        st.warning(f"⚠️ **Missing Dependencies:** {', '.join(missing_deps)}")
        st.info("Please install missing dependencies:")
        st.code(f"pip install {' '.join(missing_deps)}")
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'current_dataset' not in st.session_state:
        st.session_state.current_dataset = None
    
    # Header
    st.markdown('<h1 class="main-header">📊 Multi-Agent Data Analysis System</h1>', unsafe_allow_html=True)
    
    # Add clear results button
    if st.session_state.analysis_results:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Clear All Results", type="secondary"):
                st.session_state.analysis_results = {}
                st.session_state.current_dataset = None
                st.rerun()
    
    # Sidebar for agent selection
    st.sidebar.title("🤖 Agent Selection")
    st.sidebar.markdown("Choose which agent to run:")
    
    # Agent options
    agent_options = {
        "📋 Dataset Description Agent": "dataset_description",
        "🔍 Domain Patterns Agent": "domain_patterns", 
        "📈 Visualizations Agent": "visualizations",
        "⚙️ Custom Analysis Agent": "custom_analysis",
        "🎯 Business Goals Agent": "business_goals",
        "📊 Comprehensive Report Agent": "comprehensive_report"
    }
    
    selected_agent = st.sidebar.selectbox(
        "Select Agent:",
        options=list(agent_options.keys()),
        index=0
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Dataset Upload")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload your CSV dataset:",
            type=['csv'],
            help="Upload a CSV file to analyze with the selected agent"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
        # Display dataset preview
        try:
            # Try to read with different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df_preview = None
            
            for encoding in encodings:
                try:
                    df_preview = pd.read_csv(temp_file_path, nrows=10, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df_preview is None:
                st.error("❌ Could not read CSV file. Please check the file format and encoding.")
                return
            
            st.subheader("📋 Dataset Preview")
            st.dataframe(df_preview, use_container_width=True)
            
            # Dataset info
            full_df = pd.read_csv(temp_file_path, encoding=encoding)
            st.info(f"📊 **Dataset Info:** {len(full_df)} rows, {len(full_df.columns)} columns")
            
            # Show column types
            col_types = full_df.dtypes.to_dict()
            st.subheader("📊 Column Information")
            col_info_df = pd.DataFrame([
                {"Column": col, "Type": str(dtype), "Non-Null Count": full_df[col].count(), "Null Count": full_df[col].isnull().sum()}
                for col, dtype in col_types.items()
            ])
            st.dataframe(col_info_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error reading dataset: {e}")
            st.info("💡 **Tips:** Make sure your CSV file has proper headers and is not corrupted.")
            return
    
    with col2:
        st.header("⚙️ Configuration")
        
        # Check for API keys
        api_keys_status = check_api_keys()
        if not api_keys_status:
            st.warning("⚠️ **API Keys Missing**")
            st.info("Some agents require API keys. Set environment variables:")
            st.code("""
export GROQ_API_KEY="your_groq_key"
export PHI_API_KEY="your_phi_key" 
export OPENAI_API_KEY="your_openai_key"
            """)
            st.info("💡 **Demo Mode:** You can still run agents, but AI features will be limited.")
        
        # Analysis parameters
        limit = st.number_input(
            "Record Limit:",
            min_value=100,
            max_value=10000,
            value=1000,
            help="Maximum number of records to analyze (for performance)"
        )
        
        # Agent-specific parameters
        if agent_options[selected_agent] == "custom_analysis":
            custom_code = st.text_area(
                "Custom Analysis Code (Optional):",
                height=100,
                help="Enter custom PySpark code for advanced analysis"
            )
        else:
            custom_code = None
    
    # Run Agent Button
    if uploaded_file is not None:
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"🚀 Run {selected_agent}", type="primary", use_container_width=True):
                run_agent_analysis(
                    agent_options[selected_agent],
                    temp_file_path,
                    limit,
                    custom_code
                )
    
    # Display agent descriptions
    display_agent_descriptions()

def run_agent_analysis(agent_type, file_path, limit, custom_code=None):
    """Run the selected agent analysis."""
    
    # Create progress bar and output container
    progress_bar = st.progress(0)
    status_text = st.empty()
    output_container = st.empty()
    
    try:
        # Initialize agent based on type
        status_text.text("🔄 Initializing agent...")
        progress_bar.progress(10)
        
        if agent_type == "dataset_description":
            agent = DatasetDescriptionAgent(file_path, "csv", limit)
            output_file = "dataset_description_output.json"
            
        elif agent_type == "domain_patterns":
            agent = DomainSpecificPatternsAgent(file_path, "csv", limit)
            output_file = "domain_patterns_output.json"
            
        elif agent_type == "visualizations":
            agent = VisualizationsAgent(file_path, "csv", limit)
            output_file = "visualizations_output.json"
            
        elif agent_type == "custom_analysis":
            agent = CustomAnalysisAgent(file_path, "csv", limit)
            output_file = "custom_analysis_output.json"
            
        elif agent_type == "business_goals":
            agent = BusinessGoalsAgent(file_path, "csv", limit)
            output_file = "business_goals_output.json"
            
        elif agent_type == "comprehensive_report":
            # For comprehensive report, we need to extract dataset name from file path
            dataset_name = os.path.basename(file_path).replace('.csv', '')
            agent = ComprehensiveReportAgent(dataset_name)
            output_file = "comprehensive_report.json"
        
        status_text.text("🔄 Running analysis...")
        progress_bar.progress(30)
        
        # Capture AI agent output with better formatting
        with CleanOutputCapture() as capture:
            # Run the agent
            if agent_type == "custom_analysis" and custom_code:
                result = agent.execute_custom_analysis(custom_code)
            elif agent_type == "comprehensive_report":
                result = agent.generate_comprehensive_report()
            else:
                result = agent.save_output(output_file)
        
        # Display AI agent output
        ai_output = capture.get_clean_output()
        if ai_output.strip():
            with output_container.container():
                st.subheader("🤖 AI Agent Analysis Output")
                # Display as terminal-style output
                st.code(ai_output, language="text")
        else:
            # Show a message if no output was captured
            with output_container.container():
                st.info("ℹ️ AI agent completed analysis. Check the results section below for detailed output.")
        
        status_text.text("🔄 Processing results...")
        progress_bar.progress(80)
        
        # Display results
        display_agent_results(agent_type, result, output_file)
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis completed successfully!")
        
        # Cleanup
        agent.cleanup()
        
        # Clean up temporary files
        cleanup_temp_files()
        
    except Exception as e:
        st.error(f"❌ Error running {agent_type} agent: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Analysis failed")
        
        # Try fallback analysis
        st.info("🔄 Attempting fallback analysis...")
        try:
            fallback_result = get_fallback_analysis(file_path, "csv", limit)
            if fallback_result and not fallback_result.get("error"):
                st.success("✅ Fallback analysis completed!")
                display_agent_results(agent_type, fallback_result, "fallback_output.json")
                return
        except Exception as fallback_error:
            st.error(f"❌ Fallback analysis also failed: {fallback_error}")
        
        # Show error details
        with output_container.container():
            st.subheader("❌ Error Details")
            st.code(str(e))
            
            # Provide helpful error messages
            if "No module named" in str(e):
                st.error("💡 **Solution:** Make sure all required packages are installed. Run: `pip install -r streamlit_requirements.txt`")
            elif "API" in str(e) or "key" in str(e).lower():
                st.error("💡 **Solution:** Check your API keys. Make sure GROQ_API_KEY, PHI_API_KEY, and OPENAI_API_KEY are set.")
            elif "file" in str(e).lower() and "not found" in str(e).lower():
                st.error("💡 **Solution:** Make sure the uploaded file is a valid CSV file.")
            else:
                st.info("💡 **General Tips:** Check the console logs for more detailed error information.")

def display_agent_results(agent_type, result, output_file):
    """Display the results of the agent analysis."""
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Agent-specific result display
    if agent_type == "dataset_description":
        display_dataset_description_results(result)
        
    elif agent_type == "domain_patterns":
        display_domain_patterns_results(result)
        
    elif agent_type == "visualizations":
        display_visualizations_results(result)
        
    elif agent_type == "custom_analysis":
        display_custom_analysis_results(result)
        
    elif agent_type == "business_goals":
        display_business_goals_results(result)
        
    elif agent_type == "comprehensive_report":
        display_comprehensive_report_results(result)
    
    # Download results
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            json_data = f.read()
        
        st.download_button(
            label="📥 Download Results (JSON)",
            data=json_data,
            file_name=output_file,
            mime="application/json"
        )

def display_dataset_description_results(result):
    """Display dataset description results."""
    st.subheader("📋 Dataset Description Results")
    
    if isinstance(result, dict):
        # Dataset overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", result.get('total_records', 'N/A'))
        with col2:
            st.metric("Total Columns", len(result.get('schema_analysis', {}).get('column_names', [])))
        with col3:
            st.metric("Data Quality Score", "Good" if result.get('data_quality', {}).get('duplicate_records', 0) < 100 else "Needs Review")
        
        # Column information
        if 'schema_analysis' in result:
            st.subheader("📊 Column Information")
            columns_info = result['schema_analysis']['column_names']
            st.write(f"**Columns:** {', '.join(columns_info)}")
        
        # Data quality
        if 'data_quality' in result:
            st.subheader("🔍 Data Quality Assessment")
            quality_data = result['data_quality']
            
            if 'null_counts' in quality_data:
                null_df = pd.DataFrame(list(quality_data['null_counts'].items()), 
                                     columns=['Column', 'Null Count'])
                st.dataframe(null_df, use_container_width=True)

def display_domain_patterns_results(result):
    """Display domain patterns results."""
    st.subheader("🔍 Domain Patterns Analysis Results")
    
    if isinstance(result, dict) and 'analysis_data' in result:
        analysis_data = result['analysis_data']
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", analysis_data.get('total_records', 'N/A'))
        with col2:
            st.metric("Numeric Columns", len(analysis_data.get('column_types', {}).get('numeric_columns', [])))
        with col3:
            st.metric("Date Columns", len(analysis_data.get('column_types', {}).get('date_columns', [])))
        
        # Correlations
        if 'correlations' in analysis_data and analysis_data['correlations']:
            st.subheader("📈 Correlation Analysis")
            correlations = analysis_data['correlations']
            
            # Create correlation matrix for visualization
            if correlations:
                corr_data = []
                for col1, col2_dict in correlations.items():
                    for col2, corr_value in col2_dict.items():
                        corr_data.append({'Column 1': col1, 'Column 2': col2, 'Correlation': corr_value})
                
                if corr_data:
                    corr_df = pd.DataFrame(corr_data)
                    st.dataframe(corr_df, use_container_width=True)

def display_visualizations_results(result):
    """Display visualizations results."""
    st.subheader("📈 Visualizations Results")
    
    if isinstance(result, dict):
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Visualizations", result.get('visualization_count', 0))
        with col2:
            st.metric("AI Recommended", result.get('ai_recommended_count', 0))
        with col3:
            st.metric("Standard Charts", result.get('standard_count', 0))
        
        # Display generated images
        if 'visualizations' in result:
            st.subheader("🖼️ Generated Visualizations")
            
            for viz_name, viz_info in result['visualizations'].items():
                if isinstance(viz_info, dict) and 'file_path' in viz_info:
                    file_path = viz_info['file_path']
                    if os.path.exists(file_path):
                        st.subheader(f"📊 {viz_name}")
                        st.image(file_path, use_column_width=True)
                        st.caption(viz_info.get('description', ''))

def display_custom_analysis_results(result):
    """Display custom analysis results."""
    st.subheader("⚙️ Custom Analysis Results")
    
    if isinstance(result, dict):
        # Analysis type
        analysis_type = result.get('analysis_results', {}).get('analysis_type', 'unknown')
        st.info(f"**Analysis Type:** {analysis_type}")
        
        # Statistical analysis
        if 'statistical_analysis' in result.get('analysis_results', {}):
            st.subheader("📊 Statistical Analysis")
            stats = result['analysis_results']['statistical_analysis']
            
            for col_name, col_stats in stats.items():
                if isinstance(col_stats, dict) and 'basic_stats' in col_stats:
                    st.write(f"**{col_name}:**")
                    stats_df = pd.DataFrame(list(col_stats['basic_stats'].items()), 
                                          columns=['Statistic', 'Value'])
                    st.dataframe(stats_df, use_container_width=True)

def display_business_goals_results(result):
    """Display business goals results."""
    st.subheader("🎯 Business Goals Analysis Results")
    
    if isinstance(result, dict):
        # Business metrics
        if 'business_metrics' in result:
            metrics = result['business_metrics']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Revenue Columns", len(metrics.get('revenue_columns', [])))
            with col2:
                st.metric("Customer Columns", len(metrics.get('customer_columns', [])))
            with col3:
                st.metric("Time Columns", len(metrics.get('time_columns', [])))
        
        # Revenue analysis
        if 'revenue_analysis' in result and result['revenue_analysis']:
            st.subheader("💰 Revenue Analysis")
            revenue_data = result['revenue_analysis']
            
            for col_name, col_data in revenue_data.items():
                if isinstance(col_data, dict) and 'total_revenue' in col_data:
                    st.write(f"**{col_name}:** Total Revenue = {col_data['total_revenue']}")

def display_comprehensive_report_results(result):
    """Display comprehensive report results."""
    st.subheader("📊 Comprehensive Report Results")
    
    if isinstance(result, dict):
        # Report metadata
        if 'report_metadata' in result:
            metadata = result['report_metadata']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dataset", metadata.get('dataset_name', 'N/A'))
            with col2:
                st.metric("Agents Used", len(metadata.get('agents_used', [])))
            with col3:
                st.metric("Report Version", metadata.get('report_version', 'N/A'))
        
        # Key insights
        if 'key_insights' in result:
            st.subheader("🔍 Key Insights")
            insights = result['key_insights']
            
            if 'dataset_overview' in insights:
                overview = insights['dataset_overview']
                st.write(f"**Total Records:** {overview.get('total_records', 'N/A')}")
                st.write(f"**Columns:** {', '.join(overview.get('columns', []))}")

def display_agent_descriptions():
    """Display descriptions of all available agents."""
    st.markdown("---")
    st.header("🤖 Available Agents")
    
    agents_info = [
        {
            "name": "📋 Dataset Description Agent",
            "description": "Generates comprehensive business and technical dataset descriptions",
            "features": ["Schema analysis", "Data quality assessment", "Business context identification"]
        },
        {
            "name": "🔍 Domain Patterns Agent", 
            "description": "Analyzes domain-specific patterns, correlations, and temporal trends",
            "features": ["Correlation analysis", "Temporal patterns", "Business recommendations"]
        },
        {
            "name": "📈 Visualizations Agent",
            "description": "Creates domain-appropriate visualizations with AI-powered recommendations",
            "features": ["Business-focused charts", "AI analysis", "Professional styling"]
        },
        {
            "name": "⚙️ Custom Analysis Agent",
            "description": "Executes advanced statistical analysis, machine learning, and custom PySpark code",
            "features": ["Statistical analysis", "Machine learning", "Custom code execution"]
        },
        {
            "name": "🎯 Business Goals Agent",
            "description": "Defines business goals, revenue optimizations, and profit margin strategies",
            "features": ["Revenue analysis", "Customer behavior", "Strategic goals"]
        },
        {
            "name": "📊 Comprehensive Report Agent",
            "description": "Combines all agent outputs into executive-ready reports",
            "features": ["Executive summary", "Strategic recommendations", "Markdown reports"]
        }
    ]
    
    for agent in agents_info:
        with st.expander(agent["name"]):
            st.write(agent["description"])
            st.write("**Key Features:**")
            for feature in agent["features"]:
                st.write(f"• {feature}")

if __name__ == "__main__":
    main()
