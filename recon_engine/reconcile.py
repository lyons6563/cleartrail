"""
Reconciliation module - Matches transactions across systems.
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, Tuple, List
from difflib import SequenceMatcher

from .ingest import ingest_file
from .normalize import normalize_transactions

logger = logging.getLogger("cleartrail.engine")


def _best_candidate(
    target_amount: float,
    target_date: pd.Timestamp,
    target_reference: Optional[str],
    candidates: pd.DataFrame,
    amount_tolerance: float,
    partial_tolerance: float,
    date_window_days: int
) -> Tuple[Optional[int], Optional[str], Optional[float], Optional[int], Optional[float]]:
    if candidates.empty:
        return None, None, None, None, None

    diffs = (candidates['txn_amount'] - target_amount).abs()
    date_diffs = (candidates['txn_date'] - target_date).abs().dt.days
    percent_diff = diffs / max(abs(target_amount), 1e-9)

    exact_mask = diffs <= amount_tolerance
    partial_mask = percent_diff <= partial_tolerance

    def candidate_score(row_idx: int) -> float:
        amount_similarity = 1.0 - min(diffs.loc[row_idx] / max(abs(target_amount), 1e-9), 1.0)
        if date_diffs.loc[row_idx] == 0:
            date_score = 1.0
        elif date_diffs.loc[row_idx] <= date_window_days:
            date_score = 0.7 + 0.3 * (1 - (date_diffs.loc[row_idx] / max(date_window_days, 1)))
        else:
            date_score = 0.2
        ref_score = _reference_similarity(target_reference, candidates.loc[row_idx].get('reference'))
        return 0.55 * amount_similarity + 0.25 * date_score + 0.20 * ref_score

    if exact_mask.any():
        best_idx = max(diffs[exact_mask].index.tolist(), key=candidate_score)
        return best_idx, "Exact", diffs.loc[best_idx], int(date_diffs.loc[best_idx]), float(percent_diff.loc[best_idx])
    if partial_mask.any():
        best_idx = max(diffs[partial_mask].index.tolist(), key=candidate_score)
        return best_idx, "Partial", diffs.loc[best_idx], int(date_diffs.loc[best_idx]), float(percent_diff.loc[best_idx])

    return None, None, None, None, None


def _build_match_row(
    a_row: Optional[pd.Series],
    b_row: Optional[pd.Series],
    match_status: str,
    amount_diff: Optional[float],
    date_diff: Optional[int],
    candidate_count_a: int = 0,
    candidate_count_b: int = 0,
    duplicate_in_a: bool = False,
    duplicate_in_b: bool = False
) -> Dict[str, Any]:
    return {
        'txn_date_a': a_row.get('txn_date') if a_row is not None else None,
        'txn_amount_a': a_row.get('txn_amount') if a_row is not None else None,
        'description_a': a_row.get('description') if a_row is not None else None,
        'reference_a': a_row.get('reference') if a_row is not None else None,
        'source_file_a': a_row.get('source_file') if a_row is not None else None,
        'row_id_a': a_row.get('row_id') if a_row is not None else None,
        'txn_date_b': b_row.get('txn_date') if b_row is not None else None,
        'txn_amount_b': b_row.get('txn_amount') if b_row is not None else None,
        'description_b': b_row.get('description') if b_row is not None else None,
        'reference_b': b_row.get('reference') if b_row is not None else None,
        'source_file_b': b_row.get('source_file') if b_row is not None else None,
        'row_id_b': b_row.get('row_id') if b_row is not None else None,
        'date_delta_days': date_diff,
        'amount_delta': amount_diff,
        'match_status': match_status,
        'exception_type': 'None' if match_status == 'Exact' else 'Amount Mismatch' if match_status == 'Partial' else 'Missing Match',
        'candidate_count_a': candidate_count_a,
        'candidate_count_b': candidate_count_b,
        'duplicate_in_a': duplicate_in_a,
        'duplicate_in_b': duplicate_in_b,
        'present_in_a': a_row is not None,
        'present_in_b': b_row is not None,
        'present_in_c': False,
        'amount_a': a_row.get('txn_amount') if a_row is not None else None,
        'amount_b': b_row.get('txn_amount') if b_row is not None else None,
        'amount_c': None,
        'exception_code': None,
        'exception_label': None,
        'exception_reason': None,
        'suggested_action': None,
        'confidence_score': 0.0,
        'severity': None,
        'priority_rank': None
    }


def _match_against_system(
    base_row: pd.Series,
    candidates: pd.DataFrame,
    date_window_days: int,
    amount_tolerance: float,
    partial_tolerance: float
) -> Optional[pd.Series]:
    base_date = base_row.get('txn_date')
    base_amount = base_row.get('txn_amount')
    if pd.isna(base_date) or pd.isna(base_amount):
        return None

    date_min = base_date - pd.Timedelta(days=date_window_days)
    date_max = base_date + pd.Timedelta(days=date_window_days)
    pool = candidates[(candidates['txn_date'] >= date_min) & (candidates['txn_date'] <= date_max)]
    match_idx, match_status, _, _, _ = _best_candidate(
        base_amount, base_date, base_row.get('reference'), pool, amount_tolerance, partial_tolerance, date_window_days
    )
    if match_idx is None:
        return None
    return candidates.loc[match_idx]


def _candidate_pool(
    base_row: pd.Series,
    candidates: pd.DataFrame,
    date_window_days: int,
    partial_tolerance: float
) -> pd.DataFrame:
    base_date = base_row.get('txn_date')
    base_amount = base_row.get('txn_amount')
    if pd.isna(base_date) or pd.isna(base_amount):
        return candidates.iloc[0:0]

    date_min = base_date - pd.Timedelta(days=date_window_days)
    date_max = base_date + pd.Timedelta(days=date_window_days)
    pool = candidates[(candidates['txn_date'] >= date_min) & (candidates['txn_date'] <= date_max)]
    if pool.empty:
        return pool
    percent_diff = (pool['txn_amount'] - base_amount).abs() / max(abs(base_amount), 1e-9)
    return pool[percent_diff <= partial_tolerance]


def _duplicate_row_ids(df: pd.DataFrame) -> set:
    if df.empty:
        return set()
    ref = df['reference'].fillna('')
    keys = list(zip(df['txn_date'], df['txn_amount'], ref))
    dup_mask = pd.Series(keys).duplicated(keep=False)
    return set(df.loc[dup_mask.values, 'row_id'])


def _reference_similarity(a_ref: Optional[str], b_ref: Optional[str]) -> float:
    if not a_ref or not b_ref:
        return 0.5
    return SequenceMatcher(None, str(a_ref), str(b_ref)).ratio()


def _compute_confidence(row: pd.Series, date_window_days: int) -> float:
    amount_a = row.get('amount_a')
    amount_b = row.get('amount_b')
    amount_delta = row.get('amount_delta')
    date_delta = row.get('date_delta_days')

    if amount_a is None or amount_b is None:
        return 0.0

    base_amount = max(abs(amount_a), 1e-9)
    amount_similarity = 1.0 - min(abs(amount_delta or 0) / base_amount, 1.0)

    if date_delta is None:
        date_score = 0.0
    elif date_delta == 0:
        date_score = 1.0
    elif date_delta <= date_window_days:
        date_score = 0.7 + 0.3 * (1 - (date_delta / max(date_window_days, 1)))
    else:
        date_score = 0.2

    ref_score = _reference_similarity(row.get('reference_a'), row.get('reference_b'))

    candidate_a = row.get('candidate_count_a', 0) or 0
    candidate_b = row.get('candidate_count_b', 0) or 0
    if candidate_a <= 1 and candidate_b <= 1:
        uniqueness = 1.0
    elif candidate_a > 1 and candidate_b > 1:
        uniqueness = 0.3
    else:
        uniqueness = 0.6

    confidence = (
        0.50 * amount_similarity +
        0.20 * date_score +
        0.20 * ref_score +
        0.10 * uniqueness
    )
    return round(max(0.0, min(confidence, 1.0)), 2)


def _apply_exception_classification(df: pd.DataFrame, c_provided: bool, date_window_days: int) -> pd.DataFrame:
    def classify(row: pd.Series) -> Dict[str, str]:
        if not row.get('present_in_a'):
            return {
                "code": "missing_in_a",
                "label": "Missing in System A",
                "reason": "Record appears in other systems but not in System A.",
                "action": "Request missing export or confirm omission."
            }
        if not row.get('present_in_b'):
            return {
                "code": "missing_in_b",
                "label": "Missing in System B",
                "reason": "Record appears in System A but not in System B.",
                "action": "Request missing export or verify posting."
            }
        if c_provided and not row.get('present_in_c'):
            return {
                "code": "missing_in_c",
                "label": "Missing in System C",
                "reason": "Record appears in Systems A/B but not in System C.",
                "action": "Request System C export or verify posting."
            }
        if row.get('duplicate_in_a') or row.get('duplicate_in_b'):
            return {
                "code": "duplicate_candidate",
                "label": "Duplicate Candidate",
                "reason": "Duplicate records detected within a source system.",
                "action": "Check for duplicate export or de-duplicate source data."
            }
        if row.get('candidate_count_a', 0) > 1 and row.get('candidate_count_b', 0) > 1:
            score = row.get('confidence_score', 0.0)
            if score >= 0.85:
                if row.get('match_status') == 'Exact':
                    return {
                        "code": "exact_match",
                        "label": "Exact Match",
                        "reason": "High confidence match resolved from multiple candidates.",
                        "action": "No action required."
                    }
                return {
                    "code": "amount_mismatch",
                    "label": "Amount Mismatch",
                    "reason": "High confidence match with amount variance.",
                    "action": "Validate amounts or adjustments."
                }
            if 0.60 <= score < 0.85:
                return {
                    "code": "probable_match",
                    "label": "Probable Match",
                    "reason": "Multiple candidates exist; highest confidence match is probable.",
                    "action": "Review and confirm the suggested match."
                }
            return {
                "code": "ambiguous_match",
                "label": "Ambiguous Match",
                "reason": "Multiple candidates exist on both sides within the matching window.",
                "action": "Review candidate set and confirm the correct linkage."
            }
        if row.get('candidate_count_a', 0) > 1:
            return {
                "code": "one_to_many",
                "label": "One-to-Many",
                "reason": "One record in System A maps to multiple candidates in System B.",
                "action": "Verify batch grouping or split logic."
            }
        if row.get('candidate_count_b', 0) > 1:
            return {
                "code": "many_to_one",
                "label": "Many-to-One",
                "reason": "Multiple records in System A could map to a single System B record.",
                "action": "Verify aggregation or batch posting."
            }
        if row.get('match_status') == 'Partial':
            score = row.get('confidence_score', 0.0)
            if score >= 0.85:
                return {
                    "code": "amount_mismatch",
                    "label": "Amount Mismatch",
                    "reason": "Amounts are close but not an exact match.",
                    "action": "Validate amounts or identify adjustments."
                }
            if 0.60 <= score < 0.85:
                return {
                    "code": "probable_match",
                    "label": "Probable Match",
                    "reason": "Match is likely but amount variance exists.",
                    "action": "Review and confirm the match."
                }
            return {
                "code": "partial_match_candidate",
                "label": "Partial Match Candidate",
                "reason": "Amounts are close but confidence is low.",
                "action": "Review source records and matching rules."
            }
        if row.get('match_status') == 'Exact':
            if row.get('date_delta_days') and row.get('date_delta_days') > 0:
                if row.get('date_delta_days') <= date_window_days:
                    return {
                        "code": "date_lag_within_tolerance",
                        "label": "Date Lag (Within Tolerance)",
                        "reason": "Match found with a timing gap within the allowed window.",
                        "action": "Confirm timing is expected."
                    }
                return {
                    "code": "date_lag_outside_tolerance",
                    "label": "Date Lag (Outside Tolerance)",
                    "reason": "Match found with a timing gap beyond the allowed window.",
                    "action": "Review timing and confirm posting lag."
                }
            return {
                "code": "exact_match",
                "label": "Exact Match",
                "reason": "Amounts and dates align within tolerance.",
                "action": "No action required."
            }
        return {
            "code": "unresolved",
            "label": "Unresolved",
            "reason": "No reliable match could be determined.",
            "action": "Review source data and matching rules."
        }

    severity_map = {
        "missing_in_a": "high",
        "missing_in_b": "high",
        "missing_in_c": "high",
        "amount_mismatch": "high",
        "date_lag_outside_tolerance": "medium",
        "one_to_many": "medium",
        "many_to_one": "medium",
        "ambiguous_match": "medium",
        "probable_match": "medium",
        "partial_match_candidate": "medium",
        "duplicate_candidate": "low",
        "date_lag_within_tolerance": "low",
        "exact_match": "low",
        "unresolved": "medium"
    }

    for idx, row in df.iterrows():
        result = classify(row)
        df.at[idx, 'exception_code'] = result["code"]
        df.at[idx, 'exception_label'] = result["label"]
        df.at[idx, 'exception_reason'] = result["reason"]
        df.at[idx, 'suggested_action'] = result["action"]
        severity = severity_map.get(result["code"], "medium")
        df.at[idx, 'severity'] = severity
        amount_value = max(
            abs(row.get('amount_a') or 0),
            abs(row.get('amount_b') or 0),
            abs(row.get('amount_c') or 0)
        )
        severity_weight = {"high": 3, "medium": 2, "low": 1}.get(severity, 1)
        df.at[idx, 'priority_rank'] = severity_weight * 1_000_000 + amount_value
    return df


def reconcile_transactions(
    system_a: pd.DataFrame,
    system_b: pd.DataFrame,
    system_c: Optional[pd.DataFrame] = None,
    date_window_days: int = 3,
    amount_tolerance: float = 0.01,
    partial_tolerance: float = 0.10
) -> pd.DataFrame:
    """
    Reconcile generic transaction datasets. Optionally overlay a third system.
    """
    a = system_a.sort_values('txn_date').copy()
    b = system_b.sort_values('txn_date').copy()

    unmatched_b = set(b.index.tolist())
    rows = []

    candidate_counts_a = {}
    candidate_counts_b = {idx: 0 for idx in b.index.tolist()}
    for idx, row in a.iterrows():
        pool = _candidate_pool(row, b, date_window_days, partial_tolerance)
        candidate_counts_a[idx] = len(pool)
        for b_idx in pool.index.tolist():
            candidate_counts_b[b_idx] = candidate_counts_b.get(b_idx, 0) + 1

    dup_a = _duplicate_row_ids(a)
    dup_b = _duplicate_row_ids(b)

    for idx, row in a.iterrows():
        a_date = row['txn_date']
        a_amount = row['txn_amount']
        date_min = a_date - pd.Timedelta(days=date_window_days)
        date_max = a_date + pd.Timedelta(days=date_window_days)
        candidates = b.loc[list(unmatched_b)]
        candidates = candidates[(candidates['txn_date'] >= date_min) & (candidates['txn_date'] <= date_max)]

        match_idx, match_status, amount_diff, date_diff, percent_diff = _best_candidate(
            a_amount, a_date, row.get('reference'), candidates, amount_tolerance, partial_tolerance, date_window_days
        )

        if match_idx is None:
            rows.append(
                _build_match_row(
                    row,
                    None,
                    'Missing',
                    None,
                    None,
                    candidate_count_a=candidate_counts_a.get(idx, 0),
                    candidate_count_b=0,
                    duplicate_in_a=row.get('row_id') in dup_a,
                    duplicate_in_b=False
                )
            )
            continue

        matched = b.loc[match_idx]
        unmatched_b.discard(match_idx)
        rows.append(
            _build_match_row(
                row,
                matched,
                match_status,
                amount_diff,
                date_diff,
                candidate_count_a=candidate_counts_a.get(idx, 0),
                candidate_count_b=candidate_counts_b.get(match_idx, 0),
                duplicate_in_a=row.get('row_id') in dup_a,
                duplicate_in_b=matched.get('row_id') in dup_b
            )
        )

    for idx in unmatched_b:
        matched = b.loc[idx]
        rows.append(
            _build_match_row(
                None,
                matched,
                'Missing',
                None,
                None,
                candidate_count_a=0,
                candidate_count_b=candidate_counts_b.get(idx, 0),
                duplicate_in_a=False,
                duplicate_in_b=matched.get('row_id') in dup_b
            )
        )

    reconciled = pd.DataFrame(rows)
    if not reconciled.empty:
        reconciled['confidence_score'] = reconciled.apply(
            lambda row: _compute_confidence(row, date_window_days), axis=1
        )

    if system_c is None or system_c.empty:
        return _apply_exception_classification(reconciled, False, date_window_days)

    c = system_c.sort_values('txn_date').copy()
    for idx, row in reconciled.iterrows():
        base = None
        if row.get('present_in_a'):
            candidates = system_a[system_a['row_id'] == row.get('row_id_a')]
            if not candidates.empty:
                base = candidates.iloc[0]
        elif row.get('present_in_b'):
            candidates = system_b[system_b['row_id'] == row.get('row_id_b')]
            if not candidates.empty:
                base = candidates.iloc[0]
        if base is None:
            continue
        matched_c = _match_against_system(base, c, date_window_days, amount_tolerance, partial_tolerance)
        if matched_c is None:
            continue
        reconciled.at[idx, 'present_in_c'] = True
        reconciled.at[idx, 'amount_c'] = matched_c.get('txn_amount')

    return _apply_exception_classification(reconciled, True, date_window_days)


def run_reconciliation_from_files(
    source_file_path: str,
    deposits_file_path: str,
    date_window_days: int = 3
) -> Dict[str, Any]:
    """
    Run full reconciliation pipeline with safe error handling.
    Returns structured output instead of raising.
    """
    try:
        system_a_raw = ingest_file(source_file_path)
        system_b_raw = ingest_file(deposits_file_path)
        system_a_norm = normalize_transactions(system_a_raw)
        system_b_norm = normalize_transactions(system_b_raw)
        reconciled_df = reconcile_transactions(
            system_a_norm, system_b_norm, date_window_days=date_window_days
        )
        return {"ok": True, "remittance_df": reconciled_df}
    except Exception as exc:
        logger.exception("Reconciliation pipeline failed")
        message = str(exc) if str(exc) else "Reconciliation failed."
        return {"ok": False, "error": message}


def run_reconciliation_from_file_groups(
    system_a_files: List[str],
    system_b_files: List[str],
    system_c_files: Optional[List[str]] = None,
    date_window_days: int = 3
) -> Dict[str, Any]:
    try:
        if not system_a_files or not system_b_files:
            raise ValueError("System A and System B files are required.")
        a_frames = [normalize_transactions(ingest_file(path)) for path in system_a_files]
        b_frames = [normalize_transactions(ingest_file(path)) for path in system_b_files]
        system_a = pd.concat(a_frames, ignore_index=True)
        system_b = pd.concat(b_frames, ignore_index=True)

        system_c = None
        if system_c_files:
            c_frames = [normalize_transactions(ingest_file(path)) for path in system_c_files]
            system_c = pd.concat(c_frames, ignore_index=True)

        reconciled_df = reconcile_transactions(
            system_a, system_b, system_c=system_c, date_window_days=date_window_days
        )
        return {"ok": True, "remittance_df": reconciled_df}
    except Exception as exc:
        logger.exception("Reconciliation pipeline failed")
        message = str(exc) if str(exc) else "Reconciliation failed."
        return {"ok": False, "error": message}
