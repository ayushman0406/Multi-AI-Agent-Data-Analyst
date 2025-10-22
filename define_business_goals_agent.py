#!/usr/bin/env python
# coding: utf-8

"""
Business Goals and Revenue Optimization Agent
Defines business goals, revenue optimizations, and profit margin strategies
"""

from phi.agent import Agent
from phi.model.groq import Groq
import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, min, max, stddev, sum as spark_sum, when, isnan, isnull
from pyspark.sql.types import IntegerType, DoubleType, DateType, TimestampType, StringType
import pandas as pd
import numpy as np
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class BusinessGoalsAgent:
    def __init__(self, data_source, data_format="csv", limit=1000):
        """
        Initialize the business goals and revenue optimization agent.
        
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
            .appName("BusinessGoalsAgent") \
            .getOrCreate()
        
        # Load the dataset
        self.df = self._load_data()
        self.df.createOrReplaceTempView("dataset_sample")
        
        # Initialize the AI agent
        if Agent and Groq:
            self.agent = Agent(
                name="Business Goals and Revenue Optimization Agent",
                model=Groq(id="llama-3.3-70b-versatile"),
                instructions=[
                    "You are a specialized business analyst focused on defining business goals and revenue optimization strategies.",
                    "Analyze datasets to identify revenue opportunities, cost reduction strategies, and profit margin improvements.",
                    "Define specific, measurable business goals based on data insights.",
                    "Provide actionable recommendations for business growth and optimization.",
                    "Consider market trends, competitive advantages, and operational efficiency in your recommendations."
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
    
    def identify_business_metrics(self):
        """Identify potential business metrics from the dataset."""
        try:
            schema = self.df.schema
            column_names = [field.name for field in schema]
            column_types = {field.name: str(field.dataType) for field in schema}
            
            # Identify potential revenue-related columns
            revenue_keywords = ['revenue', 'price', 'cost', 'amount', 'total', 'fee', 'charge', 'payment', 'income', 'profit', 'margin']
            revenue_columns = [col for col in column_names if any(keyword in col.lower() for keyword in revenue_keywords)]
            
            # Identify potential customer-related columns
            customer_keywords = ['customer', 'user', 'client', 'id', 'name', 'email', 'phone', 'address']
            customer_columns = [col for col in column_names if any(keyword in col.lower() for keyword in customer_keywords)]
            
            # Identify potential time-related columns
            time_keywords = ['date', 'time', 'created', 'updated', 'timestamp', 'year', 'month', 'day']
            time_columns = [col for col in column_names if any(keyword in col.lower() for keyword in time_keywords)]
            
            # Identify potential location-related columns
            location_keywords = ['location', 'address', 'city', 'state', 'country', 'zip', 'lat', 'lon', 'latitude', 'longitude']
            location_columns = [col for col in column_names if any(keyword in col.lower() for keyword in location_keywords)]
            
            # Identify potential product/service columns
            product_keywords = ['product', 'service', 'item', 'category', 'type', 'brand', 'model']
            product_columns = [col for col in column_names if any(keyword in col.lower() for keyword in product_keywords)]
            
            return {
                "revenue_columns": revenue_columns,
                "customer_columns": customer_columns,
                "time_columns": time_columns,
                "location_columns": location_columns,
                "product_columns": product_columns,
                "all_columns": column_names,
                "column_types": column_types
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying business metrics: {e}")
            return {}
    
    def analyze_revenue_patterns(self, revenue_columns):
        """Analyze revenue patterns and opportunities."""
        try:
            revenue_analysis = {}
            
            for col_name in revenue_columns:
                try:
                    # Basic revenue statistics
                    revenue_stats = self.df.select(col_name).describe().collect()
                    stats_dict = {row[0]: row[1] for row in revenue_stats}
                    
                    # Revenue trends over time (if time columns exist)
                    time_columns = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated'])]
                    
                    if time_columns:
                        time_col = time_columns[0]  # Use first time column
                        try:
                            # Monthly revenue trend
                            monthly_revenue = self.df.groupBy(
                                col(time_col).substr(1, 7).alias("month")
                            ).agg(spark_sum(col(col_name)).alias("total_revenue")).orderBy("month").collect()
                            
                            revenue_analysis[f"{col_name}_monthly_trend"] = monthly_revenue
                        except:
                            pass
                    
                    # Top revenue sources (if categorical columns exist)
                    categorical_columns = [col for col in self.df.columns if col != col_name and col != time_col]
                    if categorical_columns:
                        try:
                            top_sources = self.df.groupBy(categorical_columns[0]).agg(
                                spark_sum(col(col_name)).alias("total_revenue"),
                                count("*").alias("transaction_count")
                            ).orderBy(col("total_revenue").desc()).limit(10).collect()
                            
                            revenue_analysis[f"{col_name}_top_sources"] = top_sources
                        except:
                            pass
                    
                    revenue_analysis[col_name] = {
                        "statistics": stats_dict,
                        "total_revenue": self.df.agg(spark_sum(col(col_name))).collect()[0][0],
                        "avg_revenue": self.df.agg(avg(col(col_name))).collect()[0][0],
                        "max_revenue": self.df.agg(max(col(col_name))).collect()[0][0],
                        "min_revenue": self.df.agg(min(col(col_name))).collect()[0][0]
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Could not analyze revenue for {col_name}: {e}")
            
            return revenue_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing revenue patterns: {e}")
            return {}
    
    def analyze_customer_behavior(self, customer_columns, revenue_columns):
        """Analyze customer behavior patterns."""
        try:
            customer_analysis = {}
            
            if customer_columns and revenue_columns:
                customer_col = customer_columns[0]  # Use first customer column
                revenue_col = revenue_columns[0]    # Use first revenue column
                
                try:
                    # Customer value analysis
                    customer_value = self.df.groupBy(customer_col).agg(
                        spark_sum(col(revenue_col)).alias("total_value"),
                        count("*").alias("transaction_count"),
                        avg(col(revenue_col)).alias("avg_transaction_value")
                    ).orderBy(col("total_value").desc())
                    
                    # Customer segmentation
                    customer_segments = customer_value.withColumn(
                        "customer_segment",
                        when(col("total_value") > customer_value.agg(avg("total_value")).collect()[0][0] * 2, "High Value")
                        .when(col("total_value") > customer_value.agg(avg("total_value")).collect()[0][0], "Medium Value")
                        .otherwise("Low Value")
                    )
                    
                    segment_distribution = customer_segments.groupBy("customer_segment").count().collect()
                    
                    customer_analysis = {
                        "customer_value_distribution": customer_value.limit(20).collect(),
                        "segment_distribution": segment_distribution,
                        "total_customers": self.df.select(customer_col).distinct().count(),
                        "avg_customer_value": customer_value.agg(avg("total_value")).collect()[0][0]
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Could not analyze customer behavior: {e}")
            
            return customer_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing customer behavior: {e}")
            return {}
    
    def generate_business_goals(self, business_metrics, revenue_analysis, customer_analysis):
        """Generate specific business goals based on data analysis."""
        try:
            goals_prompt = f"""
            Based on the following business data analysis, define specific, measurable business goals:
            
            Dataset: {self.data_source}
            Total Records: {self.df.count()}
            
            Business Metrics Identified:
            - Revenue Columns: {business_metrics.get('revenue_columns', [])}
            - Customer Columns: {business_metrics.get('customer_columns', [])}
            - Time Columns: {business_metrics.get('time_columns', [])}
            - Location Columns: {business_metrics.get('location_columns', [])}
            - Product Columns: {business_metrics.get('product_columns', [])}
            
            Revenue Analysis:
            {revenue_analysis}
            
            Customer Analysis:
            {customer_analysis}
            
            Please provide:
            
            1. REVENUE OPTIMIZATION GOALS (minimum 3):
               - Specific revenue increase targets
               - Cost reduction opportunities
               - Pricing optimization strategies
               - Market expansion goals
            
            2. CUSTOMER ACQUISITION & RETENTION GOALS:
               - Customer acquisition targets
               - Customer retention strategies
               - Customer lifetime value improvements
               - Customer satisfaction goals
            
            3. OPERATIONAL EFFICIENCY GOALS:
               - Process optimization targets
               - Resource utilization improvements
               - Automation opportunities
               - Quality improvement goals
            
            4. MARKET EXPANSION GOALS:
               - Geographic expansion opportunities
               - Product/service diversification
               - Market share growth targets
               - Competitive positioning strategies
            
            5. PROFIT MARGIN IMPROVEMENT GOALS:
               - Cost reduction strategies
               - Pricing optimization
               - Operational efficiency improvements
               - Revenue mix optimization
            
            Make sure all goals are:
            - Specific and measurable
            - Time-bound (with realistic timelines)
            - Based on actual data insights
            - Actionable with clear next steps
            """
            
            if self.agent:
                self.logger.info("Generating business goals...")
                self.agent.print_response(goals_prompt, stream=True)
            
            return "Business goals generated by the agent based on data analysis"
            
        except Exception as e:
            self.logger.error(f"Error generating business goals: {e}")
            return "Error generating business goals"
    
    def define_business_goals(self):
        """
        Define business goals and revenue optimization strategies.
        Returns:
            dict: A dictionary containing business goals and recommendations.
        """
        try:
            # Identify business metrics
            business_metrics = self.identify_business_metrics()
            
            # Analyze revenue patterns
            revenue_analysis = self.analyze_revenue_patterns(business_metrics.get("revenue_columns", []))
            
            # Analyze customer behavior
            customer_analysis = self.analyze_customer_behavior(
                business_metrics.get("customer_columns", []),
                business_metrics.get("revenue_columns", [])
            )
            
            # Generate business goals
            business_goals = self.generate_business_goals(business_metrics, revenue_analysis, customer_analysis)
            
            # Prepare result
            result = {
                "dataset_name": self.data_source,
                "total_records": self.df.count(),
                "business_metrics": business_metrics,
                "revenue_analysis": revenue_analysis,
                "customer_analysis": customer_analysis,
                "business_goals": business_goals,
                "analysis_timestamp": pd.Timestamp.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error defining business goals: {e}")
            raise
    
    def save_output(self, output_path="business_goals_output.json"):
        """Save the agent output to a JSON file."""
        try:
            result = self.define_business_goals()
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            self.logger.info(f"Business goals analysis saved to {output_path}")
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
    agent = BusinessGoalsAgent(data_source, data_format="csv", limit=1000)
    
    try:
        # Define business goals
        result = agent.save_output("business_goals_output.json")
        print("Business Goals Analysis Completed Successfully")
        print(f"Total records analyzed: {result['total_records']}")
        print(f"Revenue columns identified: {result['business_metrics'].get('revenue_columns', [])}")
        print(f"Customer columns identified: {result['business_metrics'].get('customer_columns', [])}")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        agent.cleanup()
