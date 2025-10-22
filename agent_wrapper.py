#!/usr/bin/env python
# coding: utf-8

"""
Agent Wrapper
Provides error handling and fallback functionality for agents
"""

import os
import logging
from dotenv import load_dotenv
load_dotenv()
from functools import wraps

def safe_agent_execution(agent_class):
    """Decorator to safely execute agents with fallback functionality."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in {agent_class.__name__}: {e}")
                
                # Return a fallback result
                return {
                    "error": str(e),
                    "agent_name": agent_class.__name__,
                    "fallback_mode": True,
                    "message": "Agent executed in fallback mode due to error"
                }
        return wrapper
    return decorator

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import pyspark
    except ImportError:
        missing_deps.append("pyspark")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    try:
        import seaborn
    except ImportError:
        missing_deps.append("seaborn")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import scipy
    except ImportError:
        missing_deps.append("scipy")
    
    return missing_deps

def get_fallback_analysis(data_source, data_format="csv", limit=1000):
    """Provide basic analysis when agents fail."""
    try:
        import pandas as pd
        
        # Read the data
        if data_format.lower() == "csv":
            df = pd.read_csv(data_source, nrows=limit)
        else:
            return {"error": "Only CSV format supported in fallback mode"}
        
        # Basic analysis
        result = {
            "dataset_name": data_source,
            "total_records": len(df),
            "columns": list(df.columns),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "basic_stats": df.describe().to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "fallback_mode": True,
            "message": "Basic analysis completed in fallback mode"
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "fallback_mode": True,
            "message": "Fallback analysis failed"
        }









