from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
import hashlib
import os
import subprocess


def compute_sha256(path: str) -> str:
    """
    Compute SHA-256 hash for a file path.
    """
    hash_obj = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def get_engine_commit() -> str | None:
    """
    Attempt to resolve the current git commit hash.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception:
        return None


def build_case_manifest(
    case_id: str,
    input_files: List[Dict[str, Any]],
    normalization_info: Dict[str, Any],
    reconciliation_info: Dict[str, Any],
    outputs: List[Dict[str, Any]],
    parameters: Dict[str, Any],
    engine_version: str
) -> Dict[str, Any]:
    """
    Build a reconciliation case manifest describing inputs, processing, and outputs.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    run_signature = (
        f"case_id={case_id} "
        f"inputs={len(input_files)} "
        f"outputs={len(outputs)} "
        f"params={parameters}"
    )

    manifest = {
        "case_id": case_id,
        "engine_version": engine_version,
        "timestamp_utc": timestamp,
        "input_files": input_files,
        "processing": {
            "normalization_steps": normalization_info.get("steps"),
            "detected_mappings": normalization_info.get("mappings"),
            "matching_logic": reconciliation_info.get("matching_logic"),
            "tolerances": reconciliation_info.get("tolerances"),
            "warnings": reconciliation_info.get("warnings"),
            "assumptions": reconciliation_info.get("assumptions"),
            "status": reconciliation_info.get("status"),
            "error": reconciliation_info.get("error")
        },
        "results": {
            "total_system_a": reconciliation_info.get("totals", {}).get("system_a"),
            "total_system_b": reconciliation_info.get("totals", {}).get("system_b"),
            "matched_exact": reconciliation_info.get("matched_exact"),
            "matched_fuzzy": reconciliation_info.get("matched_fuzzy"),
            "unmatched_a": reconciliation_info.get("unmatched_a"),
            "unmatched_b": reconciliation_info.get("unmatched_b"),
            "exception_count": reconciliation_info.get("exception_count"),
            "output_files": outputs
        },
        "reproducibility": {
            "parameters": parameters,
            "run_signature": run_signature,
            "engine_commit": get_engine_commit()
        }
    }
    return manifest
