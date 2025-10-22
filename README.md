# Multi-Agent Data Analysis Streamlit App

A powerful, intelligent data analysis platform featuring 6 specialized AI agents for comprehensive dataset analysis. Each agent focuses on specific aspects of data analysis - from dataset description to business insights generation.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd project
   ```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up API keys (Optional but recommended):**
   - Copy the template environment file:
   ```bash
   cp .env.template .env
   ```
   - Edit the `.env` file and add your API keys:
   ```
   GROQ_API_KEY="your_groq_api_key"
   PHI_API_KEY="your_phi_api_key"
   OPENAI_API_KEY="your_openai_api_key"
   ```

4. **Launch the application:**
   ```bash
   python run_streamlit_app.py
   ```

The app will automatically open in your browser at `http://localhost:8501`

## 🤖 Available Agents

### 1. 📋 Dataset Description Agent
- **Purpose:** Generates comprehensive business and technical dataset descriptions
- **Features:**
  - Schema analysis with column types and relationships
  - Data quality assessment (missing values, duplicates, inconsistencies)
  - Business context identification
  - Data lineage and metadata extraction

### 2. 🔍 Domain Patterns Agent
- **Purpose:** Analyzes domain-specific patterns and correlations
- **Features:**
  - Advanced correlation analysis
  - Temporal pattern identification
  - Business pattern recognition
  - Domain-specific insights extraction

### 3. 📈 Visualizations Agent
- **Purpose:** Creates domain-appropriate visualizations with AI guidance
- **Features:**
  - Automated chart type selection
  - Business-focused visual design
  - AI-powered recommendations
  - Professional styling and branding

### 4. ⚙️ Custom Analysis Agent
- **Purpose:** Executes advanced statistical analysis and custom code
- **Features:**
  - Statistical analysis (descriptive statistics, hypothesis testing)
  - Machine learning model development
  - Custom PySpark code execution
  - Performance optimization insights

### 5. 🎯 Business Goals Agent
- **Purpose:** Defines and tracks business objectives
- **Features:**
  - Revenue analysis optimization
  - Customer behavior insights
  - Strategic goal identification
  - Profit margin analysis

### 6. 📊 Comprehensive Report Agent
- **Purpose:** Generates executive-ready reports
- **Features:**
  - Executive summary compilation
  - Strategic recommendations
  - Markdown report generation
  - Cross-agent insights synthesis

## 💡 How to Use

### Basic Workflow

1. **Upload your CSV file** using the file uploader
2. **Select an agent** from the sidebar
3. **Configure your analysis** (set record limits, add custom parameters)
4. **Click "Run [Agent]"** to start analysis
5. **Review results** and download JSON output

### Advanced Features

- **Demo Mode:** Works without API keys (limited AI features)
- **Custom Analysis:** Add your own PySpark code for specialized analysis
- **Batch Analysis:** Run different agents on the same dataset
- **Result Export:** Download complete analysis results as JSON

## 🔧 Configuration

### API Keys Setup

For full AI-powered analysis, you'll need API keys for:
- **Groq API** (for primary AI processing)
- **Phi API** (for specialized tasks)
- **OpenAI API** (for alternative models)

Set as environment variables:
```bash
export GROQ_API_KEY="your_key"
export PHI_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
```

### Performance Settings

- **Record Limit:** Set maximum rows processed (default: 1000)
- **Custom Code:** Add PySpark code for advanced analytics
- **Export Options:** Select output formats and detail levels

## 📁 Project Structure

```
project/
├── run_streamlit_app.py              # Main launcher script
├── streamlit_app.py                  # Streamlit application
├── requirements.txt                   # Python dependencies
│
# Agent files
├── generate_dataset_description_agent.py
├── analyze_domain_specific_patterns_agent.py
├── generate_visualizations_agent.py
├── execute_custom_analysis_agent.py
├── define_business_goals_agent.py
├── generate_comprehensive_report_agent.py
│
# Supporting utilities
├── agent_wrapper.py                  # Fallback error handling
└── output_capture.py                 # Output formatting
```

## 🛠️ Technical Requirements

### Required Dependencies
```
pyspark==3.5.0
pandas==2.1.4
matplotlib==3.8.2
seaborn==0.13.0
numpy
scipy
openpyxl==3.1.2
python-dotenv==1.0.0
phidata
groq
```

### Additional Dependencies
The app also requires:
- `streamlit` (automatically installed)
- `plotly` (for visualizations)
- Additional dependencies managed by phidata

### Minimum System Requirements
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 500MB for environment
- **CPU:** Multi-core processor recommended

## 📊 Supported Data Formats

- **CSV Files:** Primary supported format
- **File Size:** Up to 10,000 rows (configurable)
- **Encoding:** UTF-8, Latin-1, CP1252, ISO-8859-1
- **Remaining formats:** Extensions planned for Excel, JSON

## 🔍 Troubleshooting

### Common Issues

1. **"Agents Not Available" error**
   - Ensure all agent files are present
   - Check import paths
   - Verify all dependencies installed

2. **API Key errors**
   - Check environment variable setting
   - Verify API key format and validity
   - Ensure internet connectivity

3. **File Upload issues**
   - Verify file is valid CSV format
   - Check file encoding
   - Ensure file size is within limits

4. **Memory issues with large datasets**
   - Reduce record limit in configuration
   - Use custom code for efficient processing
   - Consider dataset sampling

### Error Recovery
The app includes fallback analysis if the primary agent fails, ensuring you always get useful insights.

## 🚦 Runtime Behavior

### Performance
- **Start time:** ~30-60 seconds (first run)
- **Analysis time:** 30 seconds to 5 minutes (depending on data size)
- **Generated files:** Automatic cleanup after session

### Status Indicators
- Progress bars show analysis stages
- Clear success/error messaging
- Return-value files for download

## 🔄 Updates and Contributions

### Keeping Updated
This focused implementation includes only essential files for the Streamlit app:
- Removed Docker/conf (Dockerfile, compose files)
- Removed Documentation (multiple READMEs)
- Removed Test files
- Removed Example configurations
- Removed Sample data files

### Future Enhancements
- Additional data format support
- Real-time analysis capabilities
- Advanced visualization components
- Cloud storage integration

## 📄 License and Support

This analysis platform is designed for production data analysis. For support with:
- Installation issues
- API key configuration
- Analysis customization
- Business needs assessment

Please contact the development team.

---

**Happy analyzing! 📊**
Anything can be added to this README based on specific requirements or generated insights about the actual environment and dependencies.
