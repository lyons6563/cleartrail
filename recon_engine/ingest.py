"""
Data ingestion module - Loads and standardizes CSV inputs.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dateutil import parser
from typing import Dict, Optional, List
import warnings


def parse_date_robust(date_str, date_format=None):
    """
    Parse date string robustly, handling various formats.
    
    Args:
        date_str: Date string to parse
        date_format: Optional format string (if None, uses dateutil parser)
    
    Returns:
        Parsed datetime or None if unparseable
    """
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None
    
    try:
        if date_format:
            return pd.to_datetime(str(date_str), format=date_format)
        else:
            return parser.parse(str(date_str), dayfirst=False, yearfirst=True)
    except (ValueError, TypeError):
        try:
            return pd.to_datetime(date_str)
        except:
            warnings.warn(f"Unable to parse date: {date_str}")
            return None


def standardize_numeric(value):
    """
    Standardize numeric field, handling various formats.
    
    Args:
        value: Numeric value (string or number)
    
    Returns:
        Float or None
    """
    if pd.isna(value) or value == '' or value is None:
        return None
    
    # Remove common formatting
    if isinstance(value, str):
        value = value.replace('$', '').replace(',', '').strip()
    
    try:
        return float(value)
    except (ValueError, TypeError):
        warnings.warn(f"Unable to parse numeric: {value}")
        return None




def load_csv_with_mapping(file_path: str, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Load CSV file and apply column mapping.
    
    Args:
        file_path: Path to CSV file
        column_mapping: Dictionary mapping source columns to standard names
                       e.g., {'Employee ID': 'employee_id', 'Pay Date': 'pay_date'}
    
    Returns:
        DataFrame with standardized column names
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Apply column mapping
    mapped_cols = {}
    for source_col, target_col in column_mapping.items():
        if source_col in df.columns:
            mapped_cols[source_col] = target_col
        else:
            warnings.warn(f"Column '{source_col}' not found in file. Expected for mapping to '{target_col}'")
    
    df = df.rename(columns=mapped_cols)
    
    return df


def ingest_file(file_path: str, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Ingest a CSV file and attach source file metadata.
    """
    if column_mapping:
        df = load_csv_with_mapping(file_path, column_mapping)
    else:
        df = pd.read_csv(file_path)

    df['source_file'] = Path(file_path).name
    return df


def ingest_payroll_file(file_path: str, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Ingest payroll CSV file with optional column mapping.
    
    Args:
        file_path: Path to payroll CSV
        column_mapping: Optional column mapping dictionary
    
    Returns:
        DataFrame with standardized payroll data
    """
    return ingest_file(file_path, column_mapping)


def ingest_trust_file(file_path: str, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Ingest trust/bank CSV file with optional column mapping.
    
    Args:
        file_path: Path to trust CSV
        column_mapping: Optional column mapping dictionary
    
    Returns:
        DataFrame with standardized trust data
    """
    return ingest_file(file_path, column_mapping)


def ingest_multiple_files(file_paths: List[str], 
                         column_mapping: Optional[Dict[str, str]] = None,
                         file_type: str = 'payroll') -> pd.DataFrame:
    """
    Ingest multiple CSV files and combine into single DataFrame.
    
    Args:
        file_paths: List of file paths
        column_mapping: Optional column mapping dictionary
        file_type: 'payroll' or 'trust'
    
    Returns:
        Combined DataFrame
    """
    dfs = []
    
    for file_path in file_paths:
        if file_type == 'payroll':
            df = ingest_payroll_file(file_path, column_mapping)
        elif file_type == 'trust':
            df = ingest_trust_file(file_path, column_mapping)
        else:
            raise ValueError(f"Unknown file_type: {file_type}")
        
        dfs.append(df)
    
    if not dfs:
        return pd.DataFrame()
    
    return pd.concat(dfs, ignore_index=True)
