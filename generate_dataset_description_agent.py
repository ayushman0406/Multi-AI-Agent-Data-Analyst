#!/usr/bin/env python
# coding: utf-8

"""
Dataset Description Agent
Generates comprehensive business and technical descriptions of datasets
"""

from phi.agent import Agent
from phi.model.groq import Groq
import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, min, max, stddev
from pyspark.sql.types import IntegerType, DoubleType, DateType, TimestampType, StringType
import pandas as pd
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class DatasetDescriptionAgent:
    def __init__(self, data_source, data_format="csv", limit=1000):
        """
        Initialize the dataset description agent.
        
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
            .appName("DatasetDescriptionAgent") \
            .getOrCreate()
        
        # Load the dataset
        self.df = self._load_data()
        self.df.createOrReplaceTempView("dataset_sample")
        
        # Initialize the AI agent
        if Agent and Groq:
            self.agent = Agent(
                name="Dataset Description Agent",
                model=Groq(id="llama-3.3-70b-versatile"),
                instructions=[
                    "You are a specialized data analyst focused on generating comprehensive dataset descriptions.",
                    "Provide detailed business and technical descriptions of datasets.",
                    "Identify the domain/industry context and business relevance of the data.",
                    "Analyze data structure, quality, and relationships.",
                    "Generate actionable insights about data characteristics and potential use cases."
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
    
    def analyze_schema(self):
        """Analyze dataset schema and generate column statistics."""
        try:
            schema = self.df.schema
            column_names = [field.name for field in schema]
            column_types = {field.name: str(field.dataType) for field in schema}
            
            stats = {}
            
            for col_name in column_names:
                col_type = column_types[col_name]
                
                # Numeric statistics
                if any(type_name in col_type for type_name in ["Integer", "Double", "Float"]):
                    stats[col_name] = {
                        "type": col_type,
                        "min": self.df.agg({col_name: "min"}).collect()[0][0],
                        "max": self.df.agg({col_name: "max"}).collect()[0][0],
                        "avg": self.df.agg({col_name: "avg"}).collect()[0][0],
                        "stddev": self.df.agg({col_name: "stddev"}).collect()[0][0],
                        "null_count": self.df.filter(col(col_name).isNull()).count(),
                        "unique_values": self.df.select(col_name).distinct().count()
                    }
                
                # String statistics
                elif "String" in col_type:
                    top_values = self.df.groupBy(col_name).count().orderBy(col("count").desc()).limit(5)
                    stats[col_name] = {
                        "type": col_type,
                        "null_count": self.df.filter(col(col_name).isNull()).count(),
                        "unique_values": self.df.select(col_name).distinct().count(),
                        "top_values": top_values.collect()
                    }
                
                # Date/Timestamp statistics
                elif any(type_name in col_type for type_name in ["Date", "Timestamp"]):
                    stats[col_name] = {
                        "type": col_type,
                        "min": self.df.agg({col_name: "min"}).collect()[0][0],
                        "max": self.df.agg({col_name: "max"}).collect()[0][0],
                        "null_count": self.df.filter(col(col_name).isNull()).count()
                    }
                
                # Other types
                else:
                    stats[col_name] = {
                        "type": col_type,
                        "null_count": self.df.filter(col(col_name).isNull()).count(),
                        "unique_values": self.df.select(col_name).distinct().count()
                    }
            
            return {
                "schema": str(schema),
                "column_names": column_names,
                "column_types": column_types,
                "column_statistics": stats
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing schema: {e}")
            raise
    
    def generate_dataset_description(self):
        """
        Generate comprehensive business and technical descriptions of the dataset.
        Returns:
            dict: A dictionary containing business and technical descriptions.
        """
        try:
            # Analyze schema
            schema_analysis = self.analyze_schema()
            
            # Sample data
            sample_data = self.df.limit(10).toPandas().to_string()
            
            # Generate the agent prompt for dataset description
            description_prompt = f"""
            I need a comprehensive description of a dataset with the following characteristics:
            
            Schema:
            {schema_analysis['schema']}
            
            Column Statistics:
            {schema_analysis['column_statistics']}
            
            Sample Data:
            {sample_data}
            
            Please provide:
            
            1. BUSINESS DESCRIPTION:
               - What domain/industry does this data likely belong to?
               - What business processes or activities does this data represent?
               - Who would typically use this data and for what purposes?
               - What are the key entities and relationships in this dataset?
               - What business value does this data provide?
            
            2. TECHNICAL DESCRIPTION:
               - Detailed description of each column (what it represents, data quality, value ranges)
               - Data structure and relationships
               - Potential primary keys and foreign keys
               - Data quality assessment
               - Potential transformations needed
               - Data completeness and accuracy analysis
            
            3. DATA CHARACTERISTICS:
               - Data volume and scale
               - Temporal aspects (if applicable)
               - Geographic aspects (if applicable)
               - Categorical vs numerical data distribution
            
            Be specific and provide details based on the actual values and patterns in the data, not just the schema.
            """
            
            # Use the agent to generate descriptions
            if self.agent:
                self.logger.info("Generating dataset descriptions...")
                response = self.agent.print_response(description_prompt, stream=True)
                
                descriptions = {
                    "business_description": "Business description generated by the agent.",
                    "technical_description": "Technical description generated by the agent.",
                    "data_characteristics": "Data characteristics generated by the agent."
                }
            else:
                # Fallback without AI
                descriptions = {
                    "business_description": f"Dataset analysis for {self.data_source}",
                    "technical_description": f"Technical overview of {self.data_source}",
                    "data_characteristics": f"Data characteristics for {self.data_source}"
                }
            
            # Combine with schema analysis
            result = {
                "dataset_name": self.data_source,
                "schema_analysis": schema_analysis,
                "sample_data": sample_data,
                "descriptions": descriptions,
                "total_records": self.df.count(),
                "data_quality": {
                    "null_counts": {col_name: self.df.filter(col(col_name).isNull()).count() 
                                  for col_name in self.df.columns},
                    "duplicate_records": self.df.count() - self.df.dropDuplicates().count()
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating dataset description: {e}")
            raise
    
    def save_output(self, output_path="dataset_description_output.json"):
        """Save the agent output to a JSON file."""
        try:
            result = self.generate_dataset_description()
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            self.logger.info(f"Dataset description saved to {output_path}")
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
    agent = DatasetDescriptionAgent(data_source, data_format="csv", limit=1000)
    
    try:
        # Generate dataset description
        result = agent.save_output("dataset_description_output.json")
        print("Dataset Description Generated Successfully")
        print(f"Total records: {result['total_records']}")
        print(f"Columns: {result['schema_analysis']['column_names']}")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        agent.cleanup()
