# ClearTrail
System-agnostic reconciliation and exception intelligence engine for multi-system operations.

## What ClearTrail is
ClearTrail is a domain-neutral engine that reconciles records across multiple systems and produces structured, explainable exception outputs.

## The problem it solves
Manual reconciliation is slow, error-prone, and hard to audit. ClearTrail reduces time spent on:
- Matching records across systems with inconsistent formats
- Investigating exceptions and data integrity issues
- Building defensible evidence artifacts for operational review

## Who it is for
- Finance operations
- Data operations
- Payments teams
- Marketplaces
- SaaS operations
- Accounting
- Revenue operations

## What it does
- Ingest messy exports from multiple systems
- Normalize to a canonical transaction model
- Match records across systems
- Detect exceptions with clear labels and reasons
- Generate evidence artifacts and reproducible outputs

## Core capabilities
- Multi-system matching (A/B/C)
- Ambiguity detection and candidate grouping
- Exception classification with confidence and severity scoring
- Deterministic, reproducible CSV outputs

## Example use cases
- Payments vs. bank deposits
- Orders vs. payment processor settlements
- Invoices vs. ERP postings
- Subscriptions vs. gateway exports

## What makes it different from scripts and RPA tools
- System-agnostic normalization and matching logic
- Deterministic exception intelligence instead of brittle rule scripts
- Transparent, auditable outputs designed for operations teams

## Current status
Local web console + reconciliation engine.

## How to run it locally
1. Install dependencies: `pip install pandas python-dateutil numpy fastapi uvicorn`
2. Start the web console:
   `uvicorn web.main:app --reload`

## Folder structure
- `recon_engine/` core reconciliation engine
- `web/` local web console
- `demo_cases/` example datasets
- `run_recon.py` CLI entry point
- `_archive/` non-core historical or sample materials
