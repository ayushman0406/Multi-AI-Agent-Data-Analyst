#!/usr/bin/env python
# coding: utf-8

"""
Visualizations Generation Agent
Generates domain-appropriate visualizations for datasets
"""

from phi.agent import Agent
from phi.model.groq import Groq
import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, min, max, stddev, hour, dayofweek, month, year
from pyspark.sql.types import IntegerType, DoubleType, DateType, TimestampType, StringType
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
import base64
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class VisualizationsAgent:
    def __init__(self, data_source, data_format="csv", limit=1000):
        """
        Initialize the visualizations generation agent.
        
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
            .appName("VisualizationsAgent") \
            .getOrCreate()
        
        # Load the dataset
        self.df = self._load_data()
        self.df.createOrReplaceTempView("dataset_sample")
        
        # Initialize the AI agent
        if Agent and Groq:
            self.agent = Agent(
                name="Visualizations Generation Agent",
                model=Groq(id="llama-3.3-70b-versatile"),
                instructions=[
                    "You are a specialized data visualization expert focused on creating meaningful visualizations.",
                    "Generate appropriate visualization code for different types of data and patterns.",
                    "Create visualizations that reveal business insights and data patterns.",
                    "Provide code for distribution plots, time series, correlations, and domain-specific charts.",
                    "Ensure visualizations are clear, informative, and suitable for business presentations."
                ],
                markdown=True,
            )
        else:
            self.agent = None
            print("Warning: AI agent not available. Install phidata library for AI functionality.")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
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
        """Identify different types of columns for visualization."""
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
    
    def create_distribution_plots(self, numeric_columns):
        """Create distribution plots for numeric columns."""
        plots = {}
        
        for col_name in numeric_columns[:5]:  # Limit to 5 columns
            try:
                # Convert to pandas for plotting
                pandas_df = self.df.select(col_name).toPandas()
                
                # Create figure
                fig, axes = plt.subplots(2, 2, figsize=(12, 10))
                fig.suptitle(f'Distribution Analysis for {col_name}', fontsize=16)
                
                # Histogram
                axes[0, 0].hist(pandas_df[col_name].dropna(), bins=30, alpha=0.7, color='skyblue')
                axes[0, 0].set_title(f'Histogram of {col_name}')
                axes[0, 0].set_xlabel(col_name)
                axes[0, 0].set_ylabel('Frequency')
                
                # Box plot
                axes[0, 1].boxplot(pandas_df[col_name].dropna())
                axes[0, 1].set_title(f'Box Plot of {col_name}')
                axes[0, 1].set_ylabel(col_name)
                
                # Density plot
                pandas_df[col_name].dropna().plot(kind='density', ax=axes[1, 0], color='green')
                axes[1, 0].set_title(f'Density Plot of {col_name}')
                axes[1, 0].set_xlabel(col_name)
                
                # Q-Q plot
                from scipy import stats
                stats.probplot(pandas_df[col_name].dropna(), dist="norm", plot=axes[1, 1])
                axes[1, 1].set_title(f'Q-Q Plot of {col_name}')
                
                plt.tight_layout()
                
                # Save plot
                plot_path = f"distribution_{col_name}.png"
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                plots[col_name] = {
                    "type": "distribution",
                    "file_path": plot_path,
                    "description": f"Distribution analysis for {col_name}"
                }
                
            except Exception as e:
                self.logger.warning(f"Could not create distribution plot for {col_name}: {e}")
        
        return plots
    
    def create_correlation_heatmap(self, numeric_columns):
        """Create correlation heatmap for numeric columns."""
        if len(numeric_columns) < 2:
            return {}
        
        try:
            # Calculate correlation matrix
            pandas_df = self.df.select(numeric_columns).toPandas()
            correlation_matrix = pandas_df.corr()
            
            # Create heatmap
            plt.figure(figsize=(10, 8))
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
            plt.title('Correlation Heatmap of Numeric Variables')
            plt.tight_layout()
            
            # Save plot
            plot_path = "correlation_heatmap.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return {
                "correlation_heatmap": {
                    "type": "correlation",
                    "file_path": plot_path,
                    "description": "Correlation heatmap of numeric variables",
                    "correlation_matrix": correlation_matrix.to_dict()
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Could not create correlation heatmap: {e}")
            return {}
    
    def create_time_series_plots(self, date_columns, numeric_columns):
        """Create time series plots if date columns exist."""
        plots = {}
        
        if not date_columns or not numeric_columns:
            return plots
        
        for date_col in date_columns[:2]:  # Limit to 2 date columns
            for num_col in numeric_columns[:3]:  # Limit to 3 numeric columns
                try:
                    # Create time series data
                    time_series_df = self.df.select(date_col, num_col).toPandas()
                    time_series_df[date_col] = pd.to_datetime(time_series_df[date_col])
                    time_series_df = time_series_df.sort_values(date_col)
                    
                    # Create plot
                    plt.figure(figsize=(12, 6))
                    plt.plot(time_series_df[date_col], time_series_df[num_col], linewidth=2)
                    plt.title(f'Time Series: {num_col} over {date_col}')
                    plt.xlabel(date_col)
                    plt.ylabel(num_col)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    # Save plot
                    plot_path = f"timeseries_{date_col}_{num_col}.png"
                    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    plots[f"{date_col}_{num_col}"] = {
                        "type": "time_series",
                        "file_path": plot_path,
                        "description": f"Time series of {num_col} over {date_col}"
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Could not create time series plot for {date_col} and {num_col}: {e}")
        
        return plots
    
    def create_categorical_plots(self, categorical_columns):
        """Create plots for categorical columns."""
        plots = {}
        
        for cat_col in categorical_columns[:5]:  # Limit to 5 columns
            try:
                # Get category counts
                category_counts = self.df.groupBy(cat_col).count().orderBy(col("count").desc()).toPandas()
                
                # Create bar plot
                plt.figure(figsize=(10, 6))
                plt.bar(range(len(category_counts)), category_counts['count'])
                plt.title(f'Distribution of {cat_col}')
                plt.xlabel(cat_col)
                plt.ylabel('Count')
                plt.xticks(range(len(category_counts)), category_counts[cat_col], rotation=45)
                plt.tight_layout()
                
                # Save plot
                plot_path = f"categorical_{cat_col}.png"
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                plots[cat_col] = {
                    "type": "categorical",
                    "file_path": plot_path,
                    "description": f"Distribution of {cat_col}",
                    "category_counts": category_counts.to_dict()
                }
                
            except Exception as e:
                self.logger.warning(f"Could not create categorical plot for {cat_col}: {e}")
        
        return plots
    
    def analyze_data_with_ai(self):
        """Use AI agent to analyze the data and understand what visualizations would be most beneficial."""
        try:
            # Get sample data and basic statistics
            sample_data = self.df.limit(10).toPandas().to_string()
            column_types = self.identify_column_types()
            
            # Get basic statistics for each column
            column_stats = {}
            for col_name in self.df.columns:
                try:
                    col_type = str(self.df.schema[col_name].dataType)
                    if "Integer" in col_type or "Double" in col_type:
                        stats = self.df.select(col_name).describe().collect()
                        column_stats[col_name] = {
                            "type": col_type,
                            "stats": {row[0]: row[1] for row in stats},
                            "unique_count": self.df.select(col_name).distinct().count(),
                            "null_count": self.df.filter(col(col_name).isNull()).count()
                        }
                    elif "String" in col_type:
                        top_values = self.df.groupBy(col_name).count().orderBy(col("count").desc()).limit(5).collect()
                        column_stats[col_name] = {
                            "type": col_type,
                            "unique_count": self.df.select(col_name).distinct().count(),
                            "null_count": self.df.filter(col(col_name).isNull()).count(),
                            "top_values": top_values
                        }
                    else:
                        column_stats[col_name] = {
                            "type": col_type,
                            "unique_count": self.df.select(col_name).distinct().count(),
                            "null_count": self.df.filter(col(col_name).isNull()).count()
                        }
                except Exception as e:
                    self.logger.warning(f"Could not analyze column {col_name}: {e}")
            
            # AI analysis prompt
            analysis_prompt = f"""
            Analyze this dataset and determine the most effective visualizations for business understanding:
            
            Dataset: {self.data_source}
            Total Records: {self.df.count()}
            
            Sample Data:
            {sample_data}
            
            Column Analysis:
            {column_stats}
            
            Column Types Identified:
            - Numeric Columns: {column_types['numeric_columns']}
            - Date Columns: {column_types['date_columns']}
            - Categorical Columns: {column_types['categorical_columns']}
            
            Based on this analysis, please provide:
            
            1. BUSINESS CONTEXT ANALYSIS:
               - What type of business/domain does this data represent?
               - What are the key business metrics and KPIs?
               - What business questions can this data answer?
            
            2. RECOMMENDED VISUALIZATIONS (prioritize by business value):
               - Top 5 most important visualizations for business stakeholders
               - Specific plot types and which columns to use
               - Business insights each visualization will reveal
               - Target audience for each visualization
            
            3. VISUALIZATION STRATEGY:
               - Which visualizations should be grouped together?
               - What story do these visualizations tell?
               - How to present findings to different stakeholders (executives, analysts, operations)
            
            4. CUSTOM VISUALIZATION CODE:
               - Provide specific PySpark/pandas/matplotlib code for each recommended visualization
               - Include proper titles, labels, and styling for business presentations
               - Add business context to chart titles and annotations
            
            Focus on visualizations that will help business users make data-driven decisions.
            """
            
            if self.agent:
                self.logger.info("AI analyzing data for optimal visualizations...")
                ai_analysis = self.agent.print_response(analysis_prompt, stream=True)
                return ai_analysis
            else:
                return "AI agent not available for analysis"
                
        except Exception as e:
            self.logger.error(f"Error in AI data analysis: {e}")
            return "Error in AI analysis"

    def create_ai_recommended_visualizations(self, ai_recommendations):
        """Create visualizations based on AI recommendations."""
        try:
            # This would parse AI recommendations and create specific visualizations
            # For now, we'll create intelligent visualizations based on data analysis
            column_types = self.identify_column_types()
            visualizations = {}
            
            # Create business-focused visualizations based on column analysis
            if column_types["numeric_columns"]:
                # Create KPI-style visualizations for numeric columns
                for col_name in column_types["numeric_columns"][:3]:  # Top 3 numeric columns
                    try:
                        # Business KPI visualization
                        pandas_df = self.df.select(col_name).toPandas()
                        
                        # Create a business-focused summary plot
                        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                        fig.suptitle(f'Business Analysis: {col_name}', fontsize=16, fontweight='bold')
                        
                        # 1. Distribution with business context
                        axes[0].hist(pandas_df[col_name].dropna(), bins=20, alpha=0.7, color='#2E86AB', edgecolor='black')
                        axes[0].set_title(f'{col_name} Distribution', fontweight='bold')
                        axes[0].set_xlabel(col_name)
                        axes[0].set_ylabel('Frequency')
                        axes[0].grid(True, alpha=0.3)
                        
                        # 2. Box plot for outlier analysis
                        box_plot = axes[1].boxplot(pandas_df[col_name].dropna(), patch_artist=True)
                        box_plot['boxes'][0].set_facecolor('#A23B72')
                        axes[1].set_title(f'{col_name} - Outlier Analysis', fontweight='bold')
                        axes[1].set_ylabel(col_name)
                        axes[1].grid(True, alpha=0.3)
                        
                        # 3. Summary statistics
                        stats_text = f"""
                        Mean: {pandas_df[col_name].mean():.2f}
                        Median: {pandas_df[col_name].median():.2f}
                        Std Dev: {pandas_df[col_name].std():.2f}
                        Min: {pandas_df[col_name].min():.2f}
                        Max: {pandas_df[col_name].max():.2f}
                        """
                        axes[2].text(0.1, 0.5, stats_text, transform=axes[2].transAxes, 
                                   fontsize=12, verticalalignment='center',
                                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
                        axes[2].set_title(f'{col_name} - Key Statistics', fontweight='bold')
                        axes[2].axis('off')
                        
                        plt.tight_layout()
                        
                        # Save plot
                        plot_path = f"business_analysis_{col_name}.png"
                        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                        plt.close()
                        
                        visualizations[f"business_analysis_{col_name}"] = {
                            "type": "business_analysis",
                            "file_path": plot_path,
                            "description": f"Business analysis visualization for {col_name}",
                            "business_value": "Shows distribution, outliers, and key statistics for business decision making"
                        }
                        
                    except Exception as e:
                        self.logger.warning(f"Could not create business analysis plot for {col_name}: {e}")
            
            # Create time-based business visualizations if date columns exist
            if column_types["date_columns"] and column_types["numeric_columns"]:
                date_col = column_types["date_columns"][0]
                for num_col in column_types["numeric_columns"][:2]:
                    try:
                        # Business trend analysis
                        time_series_df = self.df.select(date_col, num_col).toPandas()
                        time_series_df[date_col] = pd.to_datetime(time_series_df[date_col])
                        time_series_df = time_series_df.sort_values(date_col)
                        
                        # Create business trend visualization
                        plt.figure(figsize=(14, 8))
                        
                        # Main trend line
                        plt.plot(time_series_df[date_col], time_series_df[num_col], 
                                linewidth=2, color='#2E86AB', alpha=0.8)
                        
                        # Add trend line
                        z = np.polyfit(range(len(time_series_df)), time_series_df[num_col], 1)
                        p = np.poly1d(z)
                        plt.plot(time_series_df[date_col], p(range(len(time_series_df))), 
                                "--", color='#A23B72', linewidth=2, label='Trend')
                        
                        # Add average line
                        avg_value = time_series_df[num_col].mean()
                        plt.axhline(y=avg_value, color='orange', linestyle=':', 
                                  linewidth=2, label=f'Average: {avg_value:.2f}')
                        
                        plt.title(f'Business Trend Analysis: {num_col} over Time', 
                                fontsize=16, fontweight='bold')
                        plt.xlabel(date_col)
                        plt.ylabel(num_col)
                        plt.legend()
                        plt.grid(True, alpha=0.3)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        
                        # Save plot
                        plot_path = f"business_trend_{date_col}_{num_col}.png"
                        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                        plt.close()
                        
                        visualizations[f"business_trend_{date_col}_{num_col}"] = {
                            "type": "business_trend",
                            "file_path": plot_path,
                            "description": f"Business trend analysis for {num_col} over {date_col}",
                            "business_value": "Shows business performance trends and patterns over time"
                        }
                        
                    except Exception as e:
                        self.logger.warning(f"Could not create business trend plot: {e}")
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating AI-recommended visualizations: {e}")
            return {}

    def generate_visualizations(self):
        """
        Generate domain-appropriate visualizations for the dataset using AI analysis.
        Returns:
            dict: A dictionary containing visualization information.
        """
        try:
            # Use AI to analyze the data and recommend visualizations
            ai_analysis = self.analyze_data_with_ai()
            
            # Create visualizations based on AI recommendations
            ai_visualizations = self.create_ai_recommended_visualizations(ai_analysis)
            
            # Also create some standard visualizations for completeness
            column_types = self.identify_column_types()
            standard_visualizations = {}
            
            # Create correlation heatmap if we have multiple numeric columns
            if len(column_types["numeric_columns"]) >= 2:
                correlation_plots = self.create_correlation_heatmap(column_types["numeric_columns"])
                standard_visualizations.update(correlation_plots)
            
            # Create categorical plots for business segmentation
            if column_types["categorical_columns"]:
                categorical_plots = self.create_categorical_plots(column_types["categorical_columns"][:3])
                standard_visualizations.update(categorical_plots)
            
            # Combine all visualizations
            all_visualizations = {
                **ai_visualizations,
                **standard_visualizations
            }
            
            # Prepare result
            result = {
                "dataset_name": self.data_source,
                "total_records": self.df.count(),
                "column_types": column_types,
                "ai_analysis": ai_analysis,
                "visualizations": all_visualizations,
                "visualization_count": len(all_visualizations),
                "ai_recommended_count": len(ai_visualizations),
                "standard_count": len(standard_visualizations),
                "business_focus": "Visualizations optimized for business understanding and decision making"
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {e}")
            raise
    
    def save_output(self, output_path="visualizations_output.json"):
        """Save the agent output to a JSON file."""
        try:
            result = self.generate_visualizations()
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            self.logger.info(f"Visualizations analysis saved to {output_path}")
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
    agent = VisualizationsAgent(data_source, data_format="csv", limit=1000)
    
    try:
        # Generate visualizations
        result = agent.save_output("visualizations_output.json")
        print("Visualizations Generated Successfully")
        print(f"Total visualizations created: {result['visualization_count']}")
        print(f"Visualization types: {list(result['visualizations'].keys())}")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        agent.cleanup()
