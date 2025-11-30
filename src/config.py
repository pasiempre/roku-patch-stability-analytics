"""
Configuration module for Roku Patch Stability Analytics
========================================================
Centralized path management and constants for reproducible ML workflows.
"""
from pathlib import Path

# ============================================================================
# 1. Project Root Definition
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================================
# 2. Data Paths
# ============================================================================
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "Raw"  # Match existing folder capitalization
PROCESSED_DATA_DIR = DATA_DIR / "Processed"  # Match existing folder capitalization

# Specific raw data files
DEVICE_EVENTS_PATH = RAW_DATA_DIR / "device_events.csv"
FIRMWARE_RELEASES_PATH = RAW_DATA_DIR / "firmware_releases.csv"
SUPPORT_TICKETS_PATH = RAW_DATA_DIR / "support_tickets.csv"

# ============================================================================
# 3. Database Paths
# ============================================================================
DB_DIR = PROJECT_ROOT / "db"
DB_PATH = DB_DIR / "roku_telemetry.db"

# ============================================================================
# 4. Model & Report Paths
# ============================================================================
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# ============================================================================
# 5. Global Constants
# ============================================================================
RANDOM_SEED = 42

# CatBoost model configuration
CATBOOST_MODEL_PATH = MODELS_DIR / "catboost_classifier_v002.cbm"
FEATURE_COLS = [
    "code_churn_score",
    "previous_version_error_rate",
    "avg_device_age_days",
    "is_hotfix",
    "patch_security",
]

# Risk threshold for CI gate
RISK_THRESHOLD = 0.50

# ============================================================================
# 6. Auto-create Required Directories
# ============================================================================
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, DB_DIR, MODELS_DIR, 
                  REPORTS_DIR, FIGURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)