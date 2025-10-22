#!/usr/bin/env python
# coding: utf-8

"""
Custom Analysis Execution Agent
Executes custom analysis code and generates advanced insights
"""

from phi.agent import Agent
from phi.model.groq import Groq
import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, min, max, stddev, sum as spark_sum, when, isnan, isnull
from pyspark.sql.types import IntegerType, DoubleType, DateType, TimestampType, StringType
from pyspark.ml.feature import VectorAssembler, StandardScaler, StringIndexer
from pyspark.ml.stat import Correlation
from pyspark.ml.clustering import KMeans
from pyspark.ml.regression import LinearRegression
from pyspark.ml.classification import LogisticRegression
import pandas as pd
import numpy as np
import json
import traceback

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class CustomAnalysisAgent:
    def __init__(self, data_source, data_format="csv", limit=1000):
        """
        Initialize the custom analysis execution agent.
        
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
            .appName("CustomAnalysisAgent") \
            .getOrCreate()
        
        # Load the dataset
        self.df = self._load_data()
        self.df.createOrReplaceTempView("dataset_sample")
        
        # Initialize the AI agent
        if Agent and Groq:
            self.agent = Agent(
                name="Custom Analysis Execution Agent",
                model=Groq(id="llama-3.3-70b-versatile"),
                instructions=[
                    "You are a specialized data scientist focused on executing custom analysis code.",
                    "Generate and execute advanced data analysis code using PySpark and ML libraries.",
                    "Perform statistical analysis, machine learning, and advanced data transformations.",
                    "Provide code for clustering, regression, classification, and other ML algorithms.",
                    "Generate insights from advanced statistical and machine learning analyses."
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
        categorical_columns = [field.name for field in schema if isinstance(field.dataType, StringType)]
        
        return {
            "numeric_columns": numeric_columns,
            "date_columns": date_columns,
            "categorical_columns": categorical_columns,
            "all_columns": [field.name for field in schema]
        }
    
    def perform_statistical_analysis(self, numeric_columns):
        """Perform advanced statistical analysis on numeric columns."""
        try:
            statistical_results = {}
            
            for col_name in numeric_columns:
                try:
                    # Basic statistics
                    stats = self.df.select(col_name).describe().collect()
                    stats_dict = {row[0]: row[1] for row in stats}
                    
                    # Additional statistics
                    additional_stats = self.df.agg(
                        spark_sum(col(col_name)).alias("sum"),
                        stddev(col(col_name)).alias("stddev"),
                        (spark_sum(col(col_name)) / count(col(col_name))).alias("mean")
                    ).collect()[0]
                    
                    # Percentiles
                    percentiles = self.df.select(col_name).toPandas()[col_name].quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).to_dict()
                    
                    statistical_results[col_name] = {
                        "basic_stats": stats_dict,
                        "additional_stats": additional_stats.asDict(),
                        "percentiles": percentiles,
                        "skewness": self._calculate_skewness(col_name),
                        "kurtosis": self._calculate_kurtosis(col_name)
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Could not perform statistical analysis for {col_name}: {e}")
            
            return statistical_results
            
        except Exception as e:
            self.logger.error(f"Error in statistical analysis: {e}")
            return {}
    
    def _calculate_skewness(self, col_name):
        """Calculate skewness for a column."""
        try:
            # Convert to pandas for skewness calculation
            pandas_df = self.df.select(col_name).toPandas()
            return float(pandas_df[col_name].skew())
        except:
            return None
    
    def _calculate_kurtosis(self, col_name):
        """Calculate kurtosis for a column."""
        try:
            # Convert to pandas for kurtosis calculation
            pandas_df = self.df.select(col_name).toPandas()
            return float(pandas_df[col_name].kurtosis())
        except:
            return None
    
    def perform_clustering_analysis(self, numeric_columns):
        """Perform clustering analysis on numeric columns."""
        try:
            if len(numeric_columns) < 2:
                return {}
            
            # Prepare data for clustering
            assembler = VectorAssembler(inputCols=numeric_columns, outputCol="features")
            df_assembled = assembler.transform(self.df.select(numeric_columns + ["*"]))
            
            # Remove rows with null values
            df_clean = df_assembled.filter(~isnull("features"))
            
            # Standardize features
            scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
            scaler_model = scaler.fit(df_clean)
            df_scaled = scaler_model.transform(df_clean)
            
            # Perform K-means clustering
            kmeans = KMeans(featuresCol="scaled_features", k=3, seed=42)
            kmeans_model = kmeans.fit(df_scaled)
            df_clustered = kmeans_model.transform(df_scaled)
            
            # Get cluster centers
            cluster_centers = kmeans_model.clusterCenters()
            
            # Get cluster distribution
            cluster_distribution = df_clustered.groupBy("prediction").count().collect()
            
            return {
                "cluster_centers": [center.tolist() for center in cluster_centers],
                "cluster_distribution": [{"cluster": row[0], "count": row[1]} for row in cluster_distribution],
                "features_used": numeric_columns,
                "model_summary": "K-means clustering with 3 clusters"
            }
            
        except Exception as e:
            self.logger.warning(f"Could not perform clustering analysis: {e}")
            return {}
    
    def perform_correlation_analysis(self, numeric_columns):
        """Perform advanced correlation analysis."""
        try:
            if len(numeric_columns) < 2:
                return {}
            
            # Prepare data
            assembler = VectorAssembler(inputCols=numeric_columns, outputCol="features")
            df_assembled = assembler.transform(self.df.select(numeric_columns))
            df_clean = df_assembled.filter(~isnull("features"))
            
            # Calculate correlation matrix
            correlation_matrix = Correlation.corr(df_clean, "features").collect()[0][0]
            correlation_array = correlation_matrix.toArray()
            
            # Convert to dictionary
            correlation_dict = {}
            for i, col1 in enumerate(numeric_columns):
                correlation_dict[col1] = {}
                for j, col2 in enumerate(numeric_columns):
                    correlation_dict[col1][col2] = float(correlation_array[i][j])
            
            return {
                "correlation_matrix": correlation_dict,
                "features_analyzed": numeric_columns
            }
            
        except Exception as e:
            self.logger.warning(f"Could not perform correlation analysis: {e}")
            return {}
    
    def generate_custom_analysis_code(self, column_types):
        """Generate custom analysis code based on the dataset."""
        try:
            analysis_prompt = f"""
            Generate custom PySpark analysis code for this dataset:
            
            Dataset: {self.data_source}
            Total Records: {self.df.count()}
            
            Column Types:
            - Numeric Columns: {column_types['numeric_columns']}
            - Date Columns: {column_types['date_columns']}
            - Categorical Columns: {column_types['categorical_columns']}
            
            Please provide:
            
            1. ADVANCED STATISTICAL ANALYSIS CODE:
               - Hypothesis testing code
               - Advanced statistical measures
               - Time series analysis (if date columns exist)
               - Anomaly detection code
            
            2. MACHINE LEARNING CODE:
               - Clustering algorithms
               - Classification models
               - Regression analysis
               - Feature engineering code
            
            3. BUSINESS INTELLIGENCE CODE:
               - KPI calculations
               - Cohort analysis
               - Customer segmentation
               - Revenue analysis
            
            4. DATA QUALITY ANALYSIS CODE:
               - Data completeness analysis
               - Data consistency checks
               - Outlier detection
               - Data validation rules
            
            Make sure all code is executable with PySpark and includes proper error handling.
            """
            
            if self.agent:
                self.logger.info("Generating custom analysis code...")
                self.agent.print_response(analysis_prompt, stream=True)
            
            return "Custom analysis code generated by the agent"
            
        except Exception as e:
            self.logger.error(f"Error generating custom analysis code: {e}")
            return "Error generating custom analysis code"
    
    def execute_custom_analysis(self, analysis_code=None):
        """
        Execute custom analysis code or generate and execute default analysis.
        Args:
            analysis_code (str): Custom PySpark code to execute (optional)
        Returns:
            dict: Results of the analysis execution.
        """
        try:
            # Identify column types
            column_types = self.identify_column_types()
            
            # Perform default analyses if no custom code provided
            if not analysis_code:
                self.logger.info("No custom code provided, performing default analyses...")
                
                # Statistical analysis
                statistical_results = self.perform_statistical_analysis(column_types["numeric_columns"])
                
                # Clustering analysis
                clustering_results = self.perform_clustering_analysis(column_types["numeric_columns"])
                
                # Correlation analysis
                correlation_results = self.perform_correlation_analysis(column_types["numeric_columns"])
                
                # Generate custom code recommendations
                custom_code = self.generate_custom_analysis_code(column_types)
                
                results = {
                    "statistical_analysis": statistical_results,
                    "clustering_analysis": clustering_results,
                    "correlation_analysis": correlation_results,
                    "custom_code_recommendations": custom_code,
                    "analysis_type": "default"
                }
            else:
                # Execute custom code
                self.logger.info("Executing custom analysis code...")
                
                # Create execution environment
                local_dict = {
                    "spark": self.spark,
                    "df": self.df,
                    "pd": pd,
                    "np": np,
                    "col": col,
                    "count": count,
                    "avg": avg,
                    "min": min,
                    "max": max,
                    "stddev": stddev,
                    "sum": spark_sum,
                    "when": when,
                    "isnan": isnan,
                    "isnull": isnull
                }
                
                # Execute the code
                exec(analysis_code, globals(), local_dict)
                
                results = {
                    "custom_code_executed": analysis_code,
                    "execution_result": local_dict.get("result", "Code executed successfully"),
                    "analysis_type": "custom"
                }
            
            # Prepare final result
            result = {
                "dataset_name": self.data_source,
                "total_records": self.df.count(),
                "column_types": column_types,
                "analysis_results": results,
                "execution_timestamp": pd.Timestamp.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing custom analysis: {e}")
            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "dataset_name": self.data_source
            }
    
    def save_output(self, output_path="custom_analysis_output.json"):
        """Save the agent output to a JSON file."""
        try:
            result = self.execute_custom_analysis()
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            self.logger.info(f"Custom analysis saved to {output_path}")
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
    agent = CustomAnalysisAgent(data_source, data_format="csv", limit=1000)
    
    try:
        # Execute custom analysis
        result = agent.save_output("custom_analysis_output.json")
        print("Custom Analysis Executed Successfully")
        print(f"Analysis type: {result['analysis_results'].get('analysis_type', 'unknown')}")
        print(f"Total records analyzed: {result['total_records']}")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        agent.cleanup()
