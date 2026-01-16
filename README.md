# ClearTrail
Core reconciliation and exception engine

## What this is
A lightweight Python engine for reconciling records across data sources and producing structured exception outputs.

## What it does
- Ingest messy data
- Normalize to a canonical model
- Match records across sources
- Generate reconciliation + exception outputs

## Core capabilities
- Flexible column aliasing and robust parsing
- Deterministic matching with confidence scoring
- Timeliness calculations and exception classification
- Audit-friendly CSV outputs and trace packs

## What this repo is NOT
- Not a product
- Not a UI
- Not a vertical solution

## Repo structure
- `recon_engine/` core reconciliation logic
- `run_recon.py` CLI entry point
- `_archive/` non-core historical or sample materials

## How to run locally (if applicable)
1. Install dependencies: `pip install pandas python-dateutil numpy`
2. Run the CLI:
   `python run_recon.py <source.csv> <deposits.csv> [ledger.csv]`
