"""Project configuration and paths.

This module is DONE for you on purpose — it's plumbing, not data engineering.
Read it so you know what's available; you shouldn't need to change much here.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env if present

ROOT = Path(__file__).resolve().parents[2]

# Landing zones (the local stand-ins for S3 bronze/silver/gold buckets)
RAW_DIR = ROOT / "data" / "raw"
STAGING_DIR = ROOT / "data" / "staging"
WAREHOUSE_DIR = ROOT / "data" / "warehouse"

GOVERNANCE_DIR = ROOT / "governance"
CONTRACTS_DIR = GOVERNANCE_DIR / "data_contracts"
RESIDENCY_POLICY = GOVERNANCE_DIR / "residency_policy.yml"

SQL_DIR = ROOT / "sql"

WAREHOUSE_PATH = Path(os.getenv("WAREHOUSE_PATH", WAREHOUSE_DIR / "passport.duckdb"))
HOME_REGION = os.getenv("HOME_REGION", "af-south-1")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Warehouse schemas (medallion layers)
BRONZE, SILVER, GOLD = "bronze", "silver", "gold"
