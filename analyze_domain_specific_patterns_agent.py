#!/usr/bin/env python
# coding: utf-8

"""
Domain-Specific Patterns Analysis Agent
Analyzes domain-specific patterns and insights based on the dataset
"""

from phi.agent import Agent
from phi.model.groq import Groq
import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, min, max, stddev, hour, dayofweek, month, year
from pyspark.sql.types import IntegerType, DoubleType, DateType, TimestampType, StringType
import pandas as pd
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class DomainSpecificPatternsAgent:
    def __init__(self, data_source, data_format="csv", limit=1000):
        """
        Initialize the domain-specific patterns analysis agent.
        
        Args:
            data_source (str): Path to the data file
            data_format (str): Format of the data file ('csv', 'parquet', 'json', etc.)
            limit (int): Maximum number of records to analyze
        """
        self.data_source = data_source
        self.data_format = data_format
        self.limit = limit
        
        # Initialize Spark session
        self.spark = SparkSession.builder \
            .appName("DomainSpecificPatternsAgent") \
            .getOrCreate()
        
        # Load the dataset
        self.df = self._load_data()
        self.df.createOrReplaceTempView("dataset_sample")
        
        # Initialize the AI agent
        if Agent and Groq:
            self.agent = Agent(
                name="Domain-Specific Patterns Analysis Agent",
                model=Groq(id="llama-3.3-70b-versatile"),
                instructions=[
                    "You are a specialized data analyst focused on identifying domain-specific patterns and insights.",
                    "Analyze data patterns, trends, anomalies, and relationships specific to the dataset's domain.",
                    "Provide business-relevant insights and recommendations based on data patterns.",
                    "Identify temporal, geographical, and categorical patterns in the data.",
                    "Generate actionable insights for business decision-making."
                ],
                markdown=True,
            )
        else:
            self.agent = None
            print("Warning: AI agent not available. Install phidata library for AI functionality.")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _load_data(self):
        """Load data based on the specified format and source."""
        try:
            if self.data_format.lower() == "csv":
                df = self.spark.read.csv(self.data_source, header=True, inferSchema=True)
            elif self.data_format.lower() == "parquet":
                df = self.spark.read.parquet(self.data_source)
            elif self.data_format.lower() == "json":
                df = self.spark.read.json(self.data_source)
            elif self.data_format.lower() == "excel":
                pandas_df = pd.read_excel(self.data_source)
                df = self.spark.createDataFrame(pandas_df)
            else:
                raise ValueError(f"Unsupported data format: {self.data_format}")
            
            if self.limit:
                df = df.limit(self.limit)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def identify_column_types(self):
        """Identify different types of columns for analysis."""
        schema = self.df.schema
        numeric_columns = [field.name for field in schema if isinstance(field.dataType, (IntegerType, DoubleType))]
        date_columns = [field.name for field in schema if isinstance(field.dataType, (DateType, TimestampType))]
        categorical_columns = [field.name for field in schema if isinstance(field.dataType, StringType) and 
                            self.df.select(field.name).distinct().count() < 50]
        
        return {
            "numeric_columns": numeric_columns,
            "date_columns": date_columns,
            "categorical_columns": categorical_columns,
            "all_columns": [field.name for field in schema]
        }
    
    def analyze_correlations(self, numeric_columns):
        """Analyze correlations between numeric columns."""
        correlations = {}
        if len(numeric_columns) >= 2:
            for i in range(len(numeric_columns)):
                for j in range(i+1, len(numeric_columns)):
                    col1 = numeric_columns[i]
                    col2 = numeric_columns[j]
                    try:
                        correlation = self.df.stat.corr(col1, col2)
                        if correlation is not None:
                            if col1 not in correlations:
                                correlations[col1] = {}
                            correlations[col1][col2] = correlation
                    except Exception as e:
                        self.logger.warning(f"Could not calculate correlation between {col1} and {col2}: {e}")
        
        return correlations
    
    def analyze_temporal_patterns(self, date_columns):
        """Analyze temporal patterns in the data."""
        temporal_patterns = {}
        
        for date_col in date_columns:
            try:
                # Hourly patterns
                hourly_data = self.df.withColumn("hour", hour(col(date_col)))
                hour_counts = hourly_data.groupBy("hour").count().orderBy("hour").collect()
                temporal_patterns[f"{date_col}_hourly"] = hour_counts
                
                # Daily patterns
                daily_data = self.df.withColumn("dayofweek", dayofweek(col(date_col)))
                day_counts = daily_data.groupBy("dayofweek").count().orderBy("dayofweek").collect()
                temporal_patterns[f"{date_col}_daily"] = day_counts
                
                # Monthly patterns
                monthly_data = self.df.withColumn("month", month(col(date_col)))
                month_counts = monthly_data.groupBy("month").count().orderBy("month").collect()
                temporal_patterns[f"{date_col}_monthly"] = month_counts
                
                # Yearly patterns
                yearly_data = self.df.withColumn("year", year(col(date_col)))
                year_counts = yearly_data.groupBy("year").count().orderBy("year").collect()
                temporal_patterns[f"{date_col}_yearly"] = year_counts
                
            except Exception as e:
                self.logger.warning(f"Could not analyze temporal patterns for {date_col}: {e}")
        
        return temporal_patterns
    
    def analyze_categorical_distributions(self, categorical_columns):
        """Analyze distributions of categorical columns."""
        category_distributions = {}
        
        for cat_col in categorical_columns:
            try:
                category_counts = self.df.groupBy(cat_col).count().orderBy(col("count").desc()).collect()
                category_distributions[cat_col] = category_counts
            except Exception as e:
                self.logger.warning(f"Could not analyze distribution for {cat_col}: {e}")
        
        return category_distributions
    
    def generate_cross_tabulations(self, categorical_columns):
        """Generate cross-tabulations for categorical columns."""
        cross_tabulations = {}
        
        if len(categorical_columns) >= 2:
            for i in range(len(categorical_columns)):
                for j in range(i+1, len(categorical_columns)):
                    col1 = categorical_columns[i]
                    col2 = categorical_columns[j]
                    try:
                        if (self.df.select(col1).distinct().count() * 
                            self.df.select(col2).distinct().count() < 100):  # Limit size
                            crosstab = self.df.crosstab(col1, col2).collect()
                            cross_tabulations[f"{col1}_{col2}"] = crosstab
                    except Exception as e:
                        self.logger.warning(f"Could not generate crosstab for {col1} and {col2}: {e}")
        
        return cross_tabulations
    
    def analyze_domain_specific_patterns(self):
        """
        Analyze domain-specific patterns and insights based on the dataset.
        Returns:
            dict: A dictionary containing domain-specific insights.
        """
        try:
            # Identify column types
            column_types = self.identify_column_types()
            
            # Analyze correlations
            correlations = self.analyze_correlations(column_types["numeric_columns"])
            
            # Analyze temporal patterns
            temporal_patterns = self.analyze_temporal_patterns(column_types["date_columns"])
            
            # Analyze categorical distributions
            category_distributions = self.analyze_categorical_distributions(column_types["categorical_columns"])
            
            # Generate cross-tabulations
            cross_tabulations = self.generate_cross_tabulations(column_types["categorical_columns"])
            
            # Prepare analysis data
            analysis_data = {
                "dataset_name": self.data_source,
                "total_records": self.df.count(),
                "column_types": column_types,
                "correlations": correlations,
                "temporal_patterns": temporal_patterns,
                "category_distributions": category_distributions,
                "cross_tabulations": cross_tabulations
            }
            
            # Generate the agent prompt for domain-specific insights
            insights_prompt = f"""
            Based on the following analysis of the dataset, provide domain-specific insights:
            
            Dataset: {self.data_source}
            Total Records: {analysis_data['total_records']}
            
            Column Types:
            - Numeric Columns: {column_types['numeric_columns']}
            - Date Columns: {column_types['date_columns']}
            - Categorical Columns: {column_types['categorical_columns']}
            
            Correlations between numeric columns:
            {correlations}
            
            Temporal patterns:
            {temporal_patterns}
            
            Category distributions:
            {category_distributions}
            
            Cross-tabulations:
            {cross_tabulations}
            
            Please provide:
            
            1. DOMAIN-SPECIFIC INSIGHTS (minimum 5):
               - Key patterns and trends in the data
               - Business implications of these patterns
               - Unusual or unexpected findings
               - Time-based patterns (if applicable)
               - Relationships between different variables
               - Seasonal or cyclical patterns
               - Geographic patterns (if applicable)
            
            2. BUSINESS RECOMMENDATIONS (minimum 3):
               - Actions that could be taken based on these insights
               - Opportunities for improvement or optimization
               - Areas requiring further investigation
               - Risk factors identified
               - Growth opportunities
            
            3. DATA QUALITY INSIGHTS:
               - Data completeness issues
               - Potential data quality problems
               - Recommendations for data cleaning
            
            4. ADVANCED ANALYSIS SUGGESTIONS:
               - Additional analyses that could be performed
               - Machine learning opportunities
               - Predictive modeling possibilities
            
            Make sure all insights are specific to this dataset and its domain, not generic data analysis recommendations.
            """
            
            # Use the agent to generate insights
            if self.agent:
                self.logger.info("Generating domain-specific insights...")
                self.agent.print_response(insights_prompt, stream=True)
            
            # Combine analysis data with insights
            result = {
                "analysis_data": analysis_data,
                "domain_insights": "Domain-specific insights generated by the agent",
                "business_recommendations": "Business recommendations generated by the agent",
                "data_quality_insights": "Data quality insights generated by the agent",
                "advanced_analysis_suggestions": "Advanced analysis suggestions generated by the agent"
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing domain-specific patterns: {e}")
            raise
    
    def save_output(self, output_path="domain_patterns_output.json"):
        """Save the agent output to a JSON file."""
        try:
            result = self.analyze_domain_specific_patterns()
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            self.logger.info(f"Domain patterns analysis saved to {output_path}")
            return result
        except Exception as e:
            self.logger.error(f"Error saving output: {e}")
            raise
    
    def cleanup(self):
        """Clean up Spark session and resources."""
        if self.spark:
            self.spark.stop()

# Usage
if __name__ == "__main__":
    # Initialize the agent with your data file
    data_source = "green_taxi_data.csv"  # Replace with your data file
    agent = DomainSpecificPatternsAgent(data_source, data_format="csv", limit=1000)
    
    try:
        # Analyze domain-specific patterns
        result = agent.save_output("domain_patterns_output.json")
        print("Domain-Specific Patterns Analysis Completed Successfully")
        print(f"Total records analyzed: {result['analysis_data']['total_records']}")
        print(f"Numeric columns: {result['analysis_data']['column_types']['numeric_columns']}")
        print(f"Date columns: {result['analysis_data']['column_types']['date_columns']}")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        agent.cleanup()
