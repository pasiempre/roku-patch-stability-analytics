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

# ============================================================================
# 6. Model Configuration & Versioning
# ============================================================================
# Model versioning strategy:
#   - v001: Initial CatBoost classifier (baseline)
#   - v002: Tuned hyperparameters, improved feature engineering (current)
#   - To promote a new version: train in notebook 03, save as v003, update path below
#   - Keep previous versions for rollback capability
CATBOOST_MODEL_PATH = MODELS_DIR / "catboost_classifier_v002.cbm"

# Features used for prediction (must match training pipeline in notebook 03)
# All features are PRE-DEPLOYMENT metrics to avoid data leakage:
#   - code_churn_score: lines_changed / days_since_release (complexity signal)
#   - previous_version_error_rate: historical error rate (regression signal)
#   - avg_device_age_days: fleet maturity at release time
#   - is_hotfix: binary flag for expedited releases (higher risk)
#   - patch_security: binary flag for security patches
FEATURE_COLS = [
    "code_churn_score",
    "previous_version_error_rate",
    "avg_device_age_days",
    "is_hotfix",
    "patch_security",
]

# ============================================================================
# 7. Risk Thresholds (with justification)
# ============================================================================
# RISK_THRESHOLD = 0.50
# Justification: Based on precision-recall tradeoff analysis in notebook 03.
# At 0.50 threshold:
#   - Precision: ~85% (low false positive rate, avoids blocking good patches)
#   - Recall: ~80% (catches most high-risk patches)
# Adjust higher (e.g., 0.70) for stricter gating, lower (e.g., 0.30) for more coverage.
RISK_THRESHOLD = 0.50

# DEVICE_AGE_THRESHOLD (used in notebook 05 for monitoring tiers)
# Justification: 600 days (~20 months) based on:
#   - Consumer electronics refresh cycle: 18-24 months typical
#   - Increased failure rates in older hardware
#   - End-of-support considerations for legacy firmware
DEVICE_AGE_THRESHOLD = 600

# ============================================================================
# 6. Auto-create Required Directories
# ============================================================================
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, DB_DIR, MODELS_DIR, 
                  REPORTS_DIR, FIGURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)