"""
Data normalization module - Converts inputs into canonical tables.
"""

import pandas as pd
from typing import Optional, Dict, List, Tuple
from .ingest import parse_date_robust, standardize_numeric
import warnings


# Column alias mappings for generic transaction data
TRANSACTION_ALIASES = {
    'txn_date': [
        'date', 'txn_date', 'transaction_date', 'post_date', 'posted_date',
        'effective_date', 'value_date', 'entry_date',
        'postdate', 'valuedate', 'bookdate', 'effectivedate', 'transdate', 'txndate'
    ],
    'txn_amount': [
        'amount', 'total', 'value', 'net_amount', 'gross_amount',
        'payment', 'charge', 'credit_amount', 'debit_amount'
    ],
    'description': [
        'memo', 'description', 'details', 'narrative', 'desc'
    ],
    'reference': [
        'reference', 'ref', 'trace', 'id', 'txn_id', 'transaction_id'
    ]
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


def _normalize_header(name: str) -> str:
    """
    Normalize header names for matching.
    """
    return (
        str(name)
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def _normalized_header_map(df: pd.DataFrame) -> Dict[str, str]:
    return {_normalize_header(col): col for col in df.columns}


def _match_alias(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    normalized_map = _normalized_header_map(df)
    for candidate in candidates:
        key = _normalize_header(candidate)
        if key in normalized_map:
            return normalized_map[key]
    return None


def _coerce_numeric_series(series: pd.Series) -> pd.Series:
    if series is None:
        return pd.Series([None] * 0)
    cleaned = series.astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
    return pd.to_numeric(cleaned, errors='coerce')


def _best_parseable_column(
    df: pd.DataFrame,
    candidates: List[str],
    parser_fn
) -> Optional[str]:
    best_col = None
    best_score = -1
    for candidate in candidates:
        col = _find_column(df, [candidate])
        if not col:
            continue
        parsed = parser_fn(df[col])
        score = parsed.notna().sum()
        if score > best_score:
            best_score = score
            best_col = col
    return best_col


def _detect_date_column(df: pd.DataFrame, candidates: List[str]) -> str:
    def _parse_series(series: pd.Series) -> pd.Series:
        return series.apply(parse_date_robust)

    direct_match = _match_alias(df, candidates)
    if direct_match:
        parsed = df[direct_match].apply(parse_date_robust)
        if parsed.isna().all():
            raise ValueError(
                "Date column could not be parsed. "
                f"Original columns: {list(df.columns)}. "
                f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
                "Examples of accepted names: date, post_date, posted_date, transaction_date, effective_date, value_date."
            )
        return direct_match

    best_col = _best_parseable_column(df, candidates, _parse_series)
    if not best_col:
        raise ValueError(
            "No recognizable date column found. "
            f"Original columns: {list(df.columns)}. "
            f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
            "Examples of accepted names: date, post_date, posted_date, transaction_date, effective_date, value_date."
        )
    parsed = df[best_col].apply(parse_date_robust)
    if parsed.isna().all():
        raise ValueError(
            "Date column could not be parsed. "
            f"Original columns: {list(df.columns)}. "
            f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
            "Examples of accepted names: date, post_date, posted_date, transaction_date, effective_date, value_date."
        )
    return best_col


def _detect_amount_series(df: pd.DataFrame) -> pd.Series:
    amount_candidates = [
        'amount', 'total', 'value', 'net_amount', 'gross_amount', 'payment', 'charge',
        'amount_usd', 'txn_amount', 'transaction_amount'
    ]
    credit_candidates = ['credit', 'credit_amount', 'cr_amount', 'amount_credit']
    debit_candidates = ['debit', 'debit_amount', 'dr_amount', 'amount_debit']

    amount_col = _match_alias(df, amount_candidates)
    if not amount_col:
        amount_col = _best_parseable_column(df, amount_candidates, _coerce_numeric_series)
    if amount_col:
        numeric_series = _coerce_numeric_series(df[amount_col])
        if numeric_series.isna().all():
            raise ValueError(
                "Amount column could not be parsed as numeric. "
                f"Original columns: {list(df.columns)}. "
                f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
                "Examples of accepted names: amount, total, value, credit_amount, debit_amount."
            )
        return numeric_series

    credit_col = _match_alias(df, credit_candidates) or _best_parseable_column(df, credit_candidates, _coerce_numeric_series)
    debit_col = _match_alias(df, debit_candidates) or _best_parseable_column(df, debit_candidates, _coerce_numeric_series)
    credit_series = _coerce_numeric_series(df[credit_col]) if credit_col else None
    debit_series = _coerce_numeric_series(df[debit_col]) if debit_col else None

    has_credit = credit_series is not None and credit_series.notna().any()
    has_debit = debit_series is not None and debit_series.notna().any()
    if not has_credit and not has_debit:
        raise ValueError(
            "No recognizable amount column found. "
            f"Original columns: {list(df.columns)}. "
            f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
            "Examples of accepted names: amount, total, value, credit_amount, debit_amount."
        )

    credit_series = credit_series.fillna(0) if credit_series is not None else 0
    debit_series = debit_series.fillna(0) if debit_series is not None else 0
    return credit_series - debit_series


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


def _build_row_id(df: pd.DataFrame, source_file_col: str, prefix: str, existing_col: str) -> pd.Series:
    """
    Build stable row identifiers per source file.
    """
    if existing_col in df.columns:
        return df[existing_col].astype(str)
    if source_file_col in df.columns:
        row_numbers = df.groupby(source_file_col).cumcount() + 1
        return (
            df[source_file_col].astype(str)
            + f":{prefix}"
            + row_numbers.map(lambda x: f"{int(x):05d}")
        )
    return pd.Series([f"{prefix}{i + 1:05d}" for i in range(len(df))], index=df.index)


def normalize_transactions(
    df: pd.DataFrame,
    date_col: Optional[str] = None,
    amount_col: Optional[str] = None,
    description_col: Optional[str] = None,
    reference_col: Optional[str] = None,
    source_file_col: str = 'source_file'
) -> pd.DataFrame:
    """
    Normalize generic transaction data into canonical format.

    Required fields:
    - txn_date
    - txn_amount
    - source_file
    """
    df = apply_column_aliases(df, TRANSACTION_ALIASES)

    if source_file_col not in df.columns:
        df[source_file_col] = 'unknown_source'

    if date_col is None:
        date_col = _detect_date_column(df, TRANSACTION_ALIASES['txn_date'])

    if amount_col is None:
        amount_series = _detect_amount_series(df)
    else:
        amount_series = _coerce_numeric_series(df[amount_col])
        if amount_series.isna().all():
            raise ValueError(
                "Amount column could not be parsed as numeric. "
                f"Original columns: {list(df.columns)}. "
                f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
                "Examples of accepted names: amount, total, value, credit_amount, debit_amount."
            )

    if description_col is None:
        description_col = _best_parseable_column(
            df,
            TRANSACTION_ALIASES['description'],
            lambda s: s.fillna('').astype(str)
        )
    if reference_col is None:
        reference_col = _best_parseable_column(
            df,
            TRANSACTION_ALIASES['reference'],
            lambda s: s.fillna('').astype(str)
        )

    normalized = pd.DataFrame()
    normalized['txn_date'] = df[date_col].apply(parse_date_robust)
    normalized['txn_amount'] = amount_series
    normalized['description'] = df[description_col] if description_col else None
    normalized['reference'] = df[reference_col] if reference_col else None
    normalized['source_file'] = df[source_file_col]
    normalized['row_id'] = _build_row_id(df, source_file_col, 'TXN', 'row_id')

    if normalized['txn_date'].isna().all():
        raise ValueError(
            "Date column could not be parsed. "
            f"Original columns: {list(df.columns)}. "
            f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
            "Examples of accepted names: date, post_date, posted_date, transaction_date, effective_date, value_date."
        )
    if normalized['txn_amount'].isna().all():
        raise ValueError(
            "Amount column could not be parsed as numeric. "
            f"Original columns: {list(df.columns)}. "
            f"Normalized columns: {list(_normalized_header_map(df).keys())}. "
            "Examples of accepted names: amount, total, value, credit_amount, debit_amount."
        )

    if normalized['txn_date'].isna().any():
        warnings.warn("Some transaction dates could not be parsed")
    if normalized['txn_amount'].isna().any():
        warnings.warn("Some transaction amounts could not be parsed")

    initial_count = len(normalized)
    normalized = normalized.dropna(subset=['txn_date', 'txn_amount'])
    removed_count = initial_count - len(normalized)
    if removed_count > 0:
        warnings.warn(f"Removed {removed_count} rows with missing txn_date or txn_amount")

    return normalized


def normalize_payroll(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Backward-compatible wrapper for legacy callers.
    """
    return normalize_transactions(df, **kwargs)


def normalize_trust(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Backward-compatible wrapper for legacy callers.
    """
    return normalize_transactions(df, **kwargs)
