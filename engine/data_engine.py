"""
DuckDB + Pandas Data Engine
Provides blazing-fast, zero-JVM in-memory SQL querying, profiling, semantic type detection,
and statistical calculations.
"""

import os
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from models.schemas import ColumnStatistic, CorrelationItem

logger = logging.getLogger(__name__)


class DataEngine:
    def __init__(self, data_source: str, limit: Optional[int] = None):
        """
        Initialize the Data Engine with a data file path.
        Supports CSV, Parquet, JSON, and Excel.
        """
        self.data_source = data_source
        self.limit = limit
        self.dataset_name = os.path.basename(data_source)
        self.con = duckdb.connect(database=":memory:")
        
        # Load data into DuckDB and cache as DataFrame
        self.df = self._load_dataset()
        self.total_rows = len(self.df)
        self.total_columns = len(self.df.columns)
        self.column_names = list(self.df.columns)

    def _load_dataset(self) -> pd.DataFrame:
        """Loads dataset into Pandas and registers in DuckDB."""
        ext = os.path.splitext(self.data_source)[1].lower()
        try:
            if ext in [".csv", ".txt"]:
                df = pd.read_csv(self.data_source, nrows=self.limit)
            elif ext in [".parquet", ".pq"]:
                df = pd.read_parquet(self.data_source)
                if self.limit:
                    df = df.head(self.limit)
            elif ext in [".json", ".jsonl"]:
                df = pd.read_json(self.data_source)
                if self.limit:
                    df = df.head(self.limit)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(self.data_source, nrows=self.limit)
            else:
                # Default attempt csv
                df = pd.read_csv(self.data_source, nrows=self.limit)
                
            # Register in DuckDB
            self.con.register("data", df)
            return df
        except Exception as e:
            logger.error(f"Failed to load dataset {self.data_source}: {e}")
            raise ValueError(f"Could not load data file '{self.data_source}': {str(e)}")

    def infer_semantic_type(self, col_name: str, dtype: str, sample_series: pd.Series) -> str:
        """Infers semantic meaning of a column based on name and value distribution."""
        col_lower = col_name.lower()
        non_null = sample_series.dropna()
        unique_cnt = non_null.nunique()
        total_cnt = len(non_null)
        
        if total_cnt == 0:
            return "unknown"

        # Check for ID / Primary Key
        if (col_lower.endswith("_id") or col_lower == "id" or "identifier" in col_lower) and unique_cnt == total_cnt:
            return "id"
            
        # Check for datetime
        if any(keyword in col_lower for keyword in ["date", "time", "timestamp", "year", "month", "day", "created_at"]):
            return "datetime"
            
        # Check for Email
        if "email" in col_lower and non_null.astype(str).str.contains("@").any():
            return "email"
            
        # Check for boolean
        if set(non_null.unique()).issubset({0, 1, True, False, "0", "1", "true", "false", "True", "False"}):
            return "boolean"
            
        # Check for Currency / Price
        if any(keyword in col_lower for keyword in ["price", "cost", "revenue", "salary", "amount", "fee", "margin", "fare", "tip"]):
            return "currency"
            
        # Numerical vs Categorical
        if np.issubdtype(sample_series.dtype, np.number):
            if unique_cnt <= 10 and total_cnt > 30:
                return "categorical"
            return "numeric_metric"
            
        if unique_cnt <= 50 or (unique_cnt / total_cnt < 0.05):
            return "categorical"
            
        return "text"

    def get_column_statistics(self) -> Dict[str, ColumnStatistic]:
        """Calculates deep column statistics in vectorized DuckDB/Pandas passes."""
        stats: Dict[str, ColumnStatistic] = {}
        total = self.total_rows if self.total_rows > 0 else 1

        for col in self.df.columns:
            series = self.df[col]
            null_count = int(series.isna().sum())
            null_pct = round((null_count / total) * 100, 2)
            unique_count = int(series.nunique())
            sem_type = self.infer_semantic_type(col, str(series.dtype), series)
            
            stat = ColumnStatistic(
                name=col,
                data_type=str(series.dtype),
                semantic_type=sem_type,
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_count
            )

            # Numeric metrics
            if np.issubdtype(series.dtype, np.number):
                valid = series.dropna()
                if not valid.empty:
                    stat.min_val = float(valid.min())
                    stat.max_val = float(valid.max())
                    stat.mean_val = round(float(valid.mean()), 3)
                    stat.stddev_val = round(float(valid.std()), 3) if len(valid) > 1 else 0.0
                    stat.median_val = round(float(valid.median()), 3)
            else:
                # Top frequent categories
                top_vals = series.value_counts().head(5).to_dict()
                stat.top_values = [{"value": str(k), "count": int(v)} for k, v in top_vals.items()]
                
            stats[col] = stat
            
        return stats

    def get_correlation_matrix(self) -> Tuple[Dict[str, Dict[str, float]], List[CorrelationItem]]:
        """Computes pairwise Pearson correlation across all numeric columns."""
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty or numeric_df.shape[1] < 2:
            return {}, []

        corr_matrix = numeric_df.corr().round(3).fillna(0.0).to_dict()
        notable_correlations: List[CorrelationItem] = []
        
        cols = list(numeric_df.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                c1, c2 = cols[i], cols[j]
                val = float(corr_matrix[c1][c2])
                abs_val = abs(val)
                
                if abs_val >= 0.3:
                    if abs_val >= 0.7:
                        strength = "very_strong"
                    elif abs_val >= 0.5:
                        strength = "strong"
                    else:
                        strength = "moderate"
                        
                    direction = "positive" if val > 0 else "inverse"
                    interp = f"{c1} and {c2} demonstrate a {strength} {direction} correlation ({val:.2f})."
                    
                    notable_correlations.append(CorrelationItem(
                        col1=c1,
                        col2=c2,
                        correlation=val,
                        strength=strength,
                        interpretation=interp
                    ))
                    
        # Sort notable correlations descending by absolute value
        notable_correlations.sort(key=lambda x: abs(x.correlation), reverse=True)
        return corr_matrix, notable_correlations

    def detect_outliers_and_anomalies(self) -> Dict[str, Any]:
        """Detects column outliers using IQR and flags data quality anomalies."""
        anomalies = []
        outlier_counts = {}
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        for col in numeric_df.columns:
            valid = numeric_df[col].dropna()
            if len(valid) > 10:
                q25 = valid.quantile(0.25)
                q75 = valid.quantile(0.75)
                iqr = q75 - q25
                if iqr > 0:
                    lower_bound = q25 - 1.5 * iqr
                    upper_bound = q75 + 1.5 * iqr
                    outliers = valid[(valid < lower_bound) | (valid > upper_bound)]
                    outlier_count = len(outliers)
                    if outlier_count > 0:
                        outlier_counts[col] = outlier_count
                        pct = round((outlier_count / len(valid)) * 100, 1)
                        if pct > 5.0:
                            anomalies.append(f"Column '{col}' exhibits significant outliers: {outlier_count} records ({pct}% of values exceed 1.5x IQR).")
                            
        # Duplicate records
        dup_count = int(self.df.duplicated().sum())
        if dup_count > 0:
            pct_dup = round((dup_count / self.total_rows) * 100, 1)
            anomalies.append(f"Found {dup_count} duplicate rows ({pct_dup}% of total dataset).")
            
        # High null percentage check
        for col in self.df.columns:
            null_count = int(self.df[col].isna().sum())
            null_pct = (null_count / self.total_rows) * 100
            if null_pct >= 20.0:
                anomalies.append(f"Column '{col}' has severe missingness: {null_count} missing rows ({null_pct:.1f}% null).")

        return {
            "duplicate_count": dup_count,
            "outlier_counts": outlier_counts,
            "anomaly_flags": anomalies
        }

    def execute_sql(self, sql: str, max_rows: int = 50) -> Dict[str, Any]:
        """Safely executes a SELECT query against the registered 'data' table."""
        clean_sql = sql.strip().strip(";")
        # Simple security guard: only allow SELECT / WITH queries
        first_token = clean_sql.split()[0].upper() if clean_sql else ""
        if first_token not in ["SELECT", "WITH", "DESCRIBE", "EXPLAIN"]:
            raise ValueError("Only read-only queries (SELECT, WITH) are permitted.")
            
        try:
            rel = self.con.sql(clean_sql)
            res_df = rel.limit(max_rows).df()
            return {
                "success": True,
                "columns": list(res_df.columns),
                "rows": res_df.to_dict(orient="records"),
                "total_returned": len(res_df)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_sample_rows(self, n: int = 10) -> List[Dict[str, Any]]:
        """Returns sample rows as a JSON-serializable list of dictionaries."""
        sample_df = self.df.head(n)
        return sample_df.replace({np.nan: None}).to_dict(orient="records")
