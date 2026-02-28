"""
CI risk-gate runner for firmware patch feature files.

This script scores firmware patches using a trained CatBoost classifier
and blocks CI pipelines when high-risk patches are detected.

Exit codes:
    0 - PASS: No high-risk patches detected
    1 - FAIL: High-risk patches detected, CI should block
    2 - ERROR: Missing file or invalid input
"""
import logging
import json
import sys
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
from catboost import CatBoostClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Add project root to path to allow importing src.config
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from src.config import CATBOOST_MODEL_PATH, FEATURE_COLS, RISK_THRESHOLD
except ImportError:
    # Fallback for standalone usage if src.config is missing
    logger.warning("Could not import src.config, using fallback values")
    FEATURE_COLS = [
        "code_churn_score",
        "previous_version_error_rate",
        "avg_device_age_days",
        "is_hotfix",
        "patch_security",
    ]
    CATBOOST_MODEL_PATH = Path("models/catboost_classifier_v002.cbm")
    RISK_THRESHOLD = 0.50


def load_model(path: Path) -> CatBoostClassifier:
    """
    Load a trained CatBoost model from disk.

    Args:
        path: Path to the .cbm model file

    Returns:
        Loaded CatBoostClassifier instance

    Raises:
        FileNotFoundError: If model file doesn't exist at path or fallback location
    """
    model = CatBoostClassifier()
    model_path = Path(path)

    if not model_path.exists():
        # Try local path if absolute fails
        local_path = Path(__file__).parent / "models" / model_path.name
        if local_path.exists():
            model_path = local_path
            logger.info(f"Using local model path: {local_path}")
        else:
            raise FileNotFoundError(f"Model file not found at {path} or {local_path}")

    logger.info(f"Loading model from {model_path}")
    model.load_model(str(model_path))
    return model


def score_file(input_csv: str) -> int:
    """
    Score firmware patches from a CSV file and determine CI gate outcome.

    Args:
        input_csv: Path to CSV file containing firmware features

    Returns:
        Exit code (0=PASS, 1=FAIL, 2=ERROR)
    """
    logger.info(f"Processing input file: {input_csv}")

    try:
        df = pd.read_csv(input_csv)
        logger.info(f"Loaded {len(df)} rows from {input_csv}")
    except FileNotFoundError:
        logger.error(f"Input features file not found at {input_csv}")
        print(f"ERROR: Input features file not found at {input_csv}")
        return 2

    # We only care about the features and the version number for output readability
    REQUIRED_FOR_RUN = FEATURE_COLS + ["firmware_version"]

    missing = [c for c in REQUIRED_FOR_RUN if c not in df.columns]
    if missing:
        # Check if it's just a naming mismatch (e.g. version vs firmware_version)
        if "version" in df.columns and "firmware_version" not in df.columns:
            df = df.rename(columns={"version": "firmware_version"})
            logger.info("Renamed 'version' column to 'firmware_version'")
            missing = [c for c in REQUIRED_FOR_RUN if c not in df.columns]

    if missing:
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"Missing required columns in {input_csv}: {missing}")

    # X is only the features used for prediction
    X = df[FEATURE_COLS]
    model = load_model(CATBOOST_MODEL_PATH)

    # Predict the probability of being the positive class (High Risk = 1)
    logger.info(f"Scoring {len(X)} patches with threshold={RISK_THRESHOLD}")
    probs = model.predict_proba(X)[:, 1]

    # Create a new output DataFrame using only the relevant data
    df_out = df[['firmware_version'] + FEATURE_COLS].copy()
    df_out["risk_score"] = probs
    df_out["high_risk_flag"] = (probs >= RISK_THRESHOLD).astype(int)

    # Save the scored file for logging/audit purposes
    output_csv = f"scored_{os.path.basename(input_csv)}"
    df_out.to_csv(output_csv, index=False)
    logger.info(f"Scored output saved to {output_csv}")

    summary = {
        "input_file": input_csv,
        "n_high_risk": int((df_out["high_risk_flag"] == 1).sum()),
        "avg_risk_score": float(df_out["risk_score"].mean())
    }

    print(json.dumps(summary, indent=2))

    # --- CI GATE LOGIC ---
    if summary["n_high_risk"] > 0:
        logger.warning(f"FAIL: {summary['n_high_risk']} high-risk patch(es) detected")
        print(f"\n🚨 FAIL: {summary['n_high_risk']} high-risk patch(es) detected. CI BLOCKED.")
        return 1
    else:
        logger.info("PASS: No high-risk patches detected")
        print("\n✅ PASS: No high-risk patches detected. CI continues.")
        return 0


if __name__ == "__main__":
    """
    Command-line entry point.

    Usage:
        python risk_gate.py path/to/new_firmware_features.csv
    """
    if len(sys.argv) < 2:
        print("Usage: python risk_gate.py path/to/new_firmware_features.csv")
        sys.exit(2)

    input_csv = sys.argv[1]
    exit_code = score_file(input_csv)
    sys.exit(exit_code)
