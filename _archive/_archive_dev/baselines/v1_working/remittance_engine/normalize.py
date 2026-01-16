"""
Data normalization module - Converts inputs into canonical tables.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from .ingest import parse_date_robust, standardize_numeric
import warnings


# Column alias mappings for common payroll/bank/recordkeeper column name variants
COLUMN_ALIASES = {
    'payroll': {
        'employee_id': ['employee_id', 'emp_id', 'Emp_ID', 'employee number', 'employee_number', 'Employee ID'],
        'pay_date': ['pay_date', 'Pay_Date', 'paydate', 'check_date', 'payroll_date'],
        'deferral_amount': ['deferral_amount', 'Deferred_Amount', '401k', '401k_amount', 'deferral', 'elective_deferral', 'EE Deferral']
    },
    'bank': {
        'deposit_id': ['deposit_id', 'Deposit_ID', 'transaction_id', 'trace_id', 'ref'],
        'deposit_date': ['deposit_date', 'Deposit_Date', 'post_date', 'transaction_date'],
        'deposit_amount': ['deposit_amount', 'Deposit_Amount', 'amount', 'credit_amount']
    },
    'trust': {
        'deposit_id': ['deposit_id', 'Deposit_ID', 'transaction_id', 'trace_id', 'ref'],
        'deposit_date': ['deposit_date', 'Deposit_Date', 'post_date', 'transaction_date'],
        'deposit_amount': ['deposit_amount', 'Deposit_Amount', 'amount', 'credit_amount']
    },
    'recordkeeper': {
        'employee_id': ['employee_id', 'Emp_ID', 'participant_id', 'Participant_ID'],
        'post_date': ['post_date', 'Post_Date', 'posted_date'],
        'posted_amount': ['posted_amount', 'Posted_Amount', 'amount']
    }
}


def apply_column_aliases(df: pd.DataFrame, aliases: Dict[str, list]) -> pd.DataFrame:
    """
    Apply column aliases to DataFrame, renaming columns to canonical names.
    
    This function lowercases and strips whitespace for matching, then renames
    columns to canonical names when a match exists. Does not error if canonical
    column is not found - that validation happens in the normalize functions.
    
    Args:
        df: Input DataFrame
        aliases: Dictionary mapping canonical column names to lists of aliases
                e.g., {'employee_id': ['emp_id', 'Emp_ID', ...]}
    
    Returns:
        DataFrame with columns renamed to canonical names (where matches found)
    """
    df = df.copy()
    
    # Create a mapping from alias to canonical name
    alias_to_canonical = {}
    for canonical_name, alias_list in aliases.items():
        # Add the canonical name itself as a valid alias
        all_aliases = [canonical_name] + alias_list
        for alias in all_aliases:
            # Normalize alias for matching: lowercase and strip whitespace
            normalized_alias = str(alias).lower().strip()
            # Only add if not already mapped (first match wins)
            if normalized_alias not in alias_to_canonical:
                alias_to_canonical[normalized_alias] = canonical_name
    
    # Build rename mapping
    rename_map = {}
    df_columns_normalized = {str(col).lower().strip(): col for col in df.columns}
    
    for normalized_alias, canonical_name in alias_to_canonical.items():
        if normalized_alias in df_columns_normalized:
            original_col = df_columns_normalized[normalized_alias]
            # Only rename if it's not already the canonical name
            if original_col != canonical_name:
                rename_map[original_col] = canonical_name
    
    # Apply renaming
    if rename_map:
        df = df.rename(columns=rename_map)
    
    return df


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Find a column in df matching any candidate (case/whitespace-insensitive).
    """
    normalized_map = {str(col).lower().strip(): col for col in df.columns}
    for candidate in candidates:
        normalized = str(candidate).lower().strip()
        if normalized in normalized_map:
            return normalized_map[normalized]
    return None


def _build_contains_mask(series: pd.Series, keywords: List[str]) -> pd.Series:
    """
    Build a case-insensitive contains mask for any keyword.
    """
    if series is None:
        return pd.Series([False] * 0)
    upper_series = series.fillna('').astype(str).str.upper()
    mask = pd.Series([False] * len(upper_series), index=upper_series.index)
    for keyword in keywords:
        mask = mask | upper_series.str.contains(keyword.upper(), na=False)
    return mask


def _match_keywords(series: pd.Series, keywords: List[str]) -> List[str]:
    """
    Return list of matched keywords for a single string value.
    """
    if series is None:
        return []
    text = str(series).upper()
    matches = [kw for kw in keywords if kw.upper() in text]
    return matches


def normalize_payroll(df: pd.DataFrame, 
                     employee_id_col: str = 'employee_id',
                     pay_date_col: str = 'pay_date',
                     deferral_amount_col: str = 'deferral_amount',
                     source_file_col: str = 'source_file') -> pd.DataFrame:
    """
    Normalize payroll data into canonical format.
    
    Required fields:
    - employee_id
    - pay_date
    - deferral_amount
    - source_file
    
    Args:
        df: Input payroll DataFrame
        employee_id_col: Column name for employee ID (used if aliases don't match)
        pay_date_col: Column name for pay date (used if aliases don't match)
        deferral_amount_col: Column name for deferral amount (used if aliases don't match)
        source_file_col: Column name for source file
    
    Returns:
        Normalized DataFrame with standard column names
    """
    # Apply column aliases first (before validation)
    payroll_aliases = {
        'employee_id': COLUMN_ALIASES['payroll']['employee_id'],
        'pay_date': COLUMN_ALIASES['payroll']['pay_date'],
        'deferral_amount': COLUMN_ALIASES['payroll']['deferral_amount']
    }
    
    # Apply aliases - this will rename matching columns to canonical names
    df = apply_column_aliases(df, payroll_aliases)
    
    # After alias mapping, check if canonical columns exist and use them if found
    if 'employee_id' in df.columns:
        employee_id_col = 'employee_id'
    if 'pay_date' in df.columns:
        pay_date_col = 'pay_date'
    if 'deferral_amount' in df.columns:
        deferral_amount_col = 'deferral_amount'
    
    # Create normalized DataFrame
    normalized = pd.DataFrame()
    
    # Map and validate required fields
    required_fields = {
        'employee_id': employee_id_col,
        'pay_date': pay_date_col,
        'deferral_amount': deferral_amount_col,
        'source_file': source_file_col
    }
    
    for standard_name, source_name in required_fields.items():
        if source_name not in df.columns:
            raise ValueError(f"Required column '{source_name}' not found in payroll data. "
                           f"Available columns: {list(df.columns)}")
        
        if standard_name == 'pay_date':
            normalized[standard_name] = df[source_name].apply(parse_date_robust)
        elif standard_name == 'deferral_amount':
            normalized[standard_name] = df[source_name].apply(standardize_numeric)
        else:
            normalized[standard_name] = df[source_name]
    
    # Validate data quality
    if normalized['deferral_amount'].isna().any():
        warnings.warn("Some deferral amounts could not be parsed")
    
    if normalized['pay_date'].isna().any():
        warnings.warn("Some pay dates could not be parsed")
    
    # Remove rows with missing critical data
    initial_count = len(normalized)
    normalized = normalized.dropna(subset=['pay_date', 'deferral_amount'])
    removed_count = initial_count - len(normalized)
    
    if removed_count > 0:
        warnings.warn(f"Removed {removed_count} rows with missing pay_date or deferral_amount")
    
    return normalized


def normalize_trust(df: pd.DataFrame,
                    deposit_id_col: str = 'deposit_id',
                    deposit_date_col: str = 'deposit_date',
                    deposit_amount_col: str = 'deposit_amount',
                    source_file_col: str = 'source_file') -> pd.DataFrame:
    """
    Normalize trust/bank data into canonical format.
    
    Required fields:
    - deposit_id
    - deposit_date
    - deposit_amount
    - source_file
    
    Args:
        df: Input trust DataFrame
        deposit_id_col: Column name for deposit ID (used if aliases don't match)
        deposit_date_col: Column name for deposit date (used if aliases don't match)
        deposit_amount_col: Column name for deposit amount (used if aliases don't match)
        source_file_col: Column name for source file
    
    Returns:
        Normalized DataFrame with standard column names
    """
    # Apply column aliases first (before validation)
    trust_aliases = {
        'deposit_id': COLUMN_ALIASES['trust']['deposit_id'],
        'deposit_date': COLUMN_ALIASES['trust']['deposit_date'],
        'deposit_amount': COLUMN_ALIASES['trust']['deposit_amount']
    }
    
    # Apply aliases - this will rename matching columns to canonical names
    df = apply_column_aliases(df, trust_aliases)
    
    # After alias mapping, check if canonical columns exist and use them if found
    if 'deposit_id' in df.columns:
        deposit_id_col = 'deposit_id'
    if 'deposit_date' in df.columns:
        deposit_date_col = 'deposit_date'
    if 'deposit_amount' in df.columns:
        deposit_amount_col = 'deposit_amount'
    
    # Transaction filtering for realistic trust statements
    transaction_type_candidates = [
        'transaction_type', 'transaction type', 'type', 'tran_type', 'transaction code'
    ]
    description_candidates = [
        'description', 'desc', 'transaction_description', 'transaction description', 'memo', 'details'
    ]
    transaction_type_col = _find_column(df, transaction_type_candidates)
    description_col = _find_column(df, description_candidates)

    include_type_values = ["CREDIT", "ACH CREDIT", "DEPOSIT"]
    include_desc_keywords = ["PAYROLL", "401K", "401(K)", "DEFERRAL", "CONTRIBUTION"]
    exclude_desc_keywords = ["FEE", "INTEREST", "REVERSAL", "RETURN", "NSF", "ADJUSTMENT"]

    if deposit_amount_col in df.columns:
        df['_deposit_amount_numeric'] = df[deposit_amount_col].apply(standardize_numeric)
    else:
        df['_deposit_amount_numeric'] = np.nan

    if transaction_type_col:
        txn_type_series = df[transaction_type_col].fillna('').astype(str).str.upper()
        include_by_type = txn_type_series.isin([v.upper() for v in include_type_values])
    else:
        include_by_type = pd.Series([False] * len(df), index=df.index)

    if description_col:
        desc_series = df[description_col].fillna('').astype(str)
        include_by_desc = _build_contains_mask(desc_series, include_desc_keywords)
        exclude_by_desc = _build_contains_mask(desc_series, exclude_desc_keywords)
    else:
        include_by_desc = pd.Series([False] * len(df), index=df.index)
        exclude_by_desc = pd.Series([False] * len(df), index=df.index)

    include_by_amount = (df['_deposit_amount_numeric'] > 0) & (~exclude_by_desc)
    include_mask = include_by_type | include_by_desc | include_by_amount
    keep_mask = include_mask & (~exclude_by_desc)

    # Build noise log with exclusion reasons
    excluded_df = df[~keep_mask].copy()
    if not excluded_df.empty:
        reasons = []
        for idx, row in excluded_df.iterrows():
            if description_col:
                matches = _match_keywords(row[description_col], exclude_desc_keywords)
                if matches:
                    reasons.append(f"Excluded: description contains {', '.join(matches)}")
                    continue
            if not include_mask.loc[idx]:
                reasons.append("Excluded: not a contribution deposit")
            else:
                reasons.append("Excluded: filtered by rule")
        excluded_df['exclusion_reason'] = reasons
    else:
        excluded_df['exclusion_reason'] = []

    # Keep only contribution-like deposits
    df = df[keep_mask].copy()

    # Clean up helper column
    if '_deposit_amount_numeric' in df.columns:
        df = df.drop(columns=['_deposit_amount_numeric'])
    if '_deposit_amount_numeric' in excluded_df.columns:
        excluded_df = excluded_df.drop(columns=['_deposit_amount_numeric'])

    # Create normalized DataFrame
    normalized = pd.DataFrame()
    
    # Map and validate required fields
    required_fields = {
        'deposit_id': deposit_id_col,
        'deposit_date': deposit_date_col,
        'deposit_amount': deposit_amount_col,
        'source_file': source_file_col
    }
    
    for standard_name, source_name in required_fields.items():
        if source_name not in df.columns:
            raise ValueError(f"Required column '{source_name}' not found in trust data. "
                           f"Available columns: {list(df.columns)}")
        
        if standard_name == 'deposit_date':
            normalized[standard_name] = df[source_name].apply(parse_date_robust)
        elif standard_name == 'deposit_amount':
            normalized[standard_name] = df[source_name].apply(standardize_numeric)
        else:
            normalized[standard_name] = df[source_name]
    
    # Validate data quality
    if normalized['deposit_amount'].isna().any():
        warnings.warn("Some deposit amounts could not be parsed")
    
    if normalized['deposit_date'].isna().any():
        warnings.warn("Some deposit dates could not be parsed")
    
    # Remove rows with missing critical data
    initial_count = len(normalized)
    normalized = normalized.dropna(subset=['deposit_date', 'deposit_amount'])
    removed_count = initial_count - len(normalized)
    
    if removed_count > 0:
        warnings.warn(f"Removed {removed_count} rows with missing deposit_date or deposit_amount")
    
    # Store noise log and summary in DataFrame attrs for downstream outputs
    normalized.attrs['trust_noise_log'] = excluded_df
    if source_file_col in normalized.columns and source_file_col in excluded_df.columns:
        kept_counts = normalized[source_file_col].value_counts().to_dict()
        excluded_counts = excluded_df[source_file_col].value_counts().to_dict()
    else:
        kept_counts = {}
        excluded_counts = {}
    normalized.attrs['trust_filter_summary'] = {
        'kept_counts': kept_counts,
        'excluded_counts': excluded_counts
    }

    return normalized
