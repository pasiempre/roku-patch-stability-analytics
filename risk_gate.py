# --- Improved risk_gate.py importing from src.config ---
import pandas as pd
import numpy as np
import json
import sys
import os
from pathlib import Path

from catboost import CatBoostClassifier

# Add project root to path to allow importing src.config
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from src.config import CATBOOST_MODEL_PATH, FEATURE_COLS, RISK_THRESHOLD
except ImportError:
    # Fallback for standalone usage if src.config is missing
    FEATURE_COLS = [
        "code_churn_score",
        "previous_version_error_rate",
        "avg_device_age_days",
        "is_hotfix",
        "patch_security",
    ]
    CATBOOST_MODEL_PATH = "models/catboost_classifier_v002.cbm"
    RISK_THRESHOLD = 0.50

def load_model(path):
    model = CatBoostClassifier()
    if not Path(path).exists():
        # Try local path if absolute fails
        local_path = Path(__file__).parent / "models" / Path(path).name
        if local_path.exists():
            path = local_path
        else:
            raise FileNotFoundError(f"Model file not found at {path} or {local_path}")
    
    model.load_model(str(path))
    return model

def score_file(input_csv: str):
    """
    Scores the input CSV, prints summary, and sets the exit code (0=PASS, 1=FAIL).
    """
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"ERROR: Input features file not found at {input_csv}")
        sys.exit(2)

    # We only care about the features and the version number for output readability
    REQUIRED_FOR_RUN = FEATURE_COLS + ["firmware_version"]

    missing = [c for c in REQUIRED_FOR_RUN if c not in df.columns]
    if missing:
        # Check if it's just a naming mismatch (e.g. version vs firmware_version)
        if "version" in df.columns and "firmware_version" not in df.columns:
            df = df.rename(columns={"version": "firmware_version"})
            missing = [c for c in REQUIRED_FOR_RUN if c not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns in {input_csv}: {missing}")

    # X is only the features used for prediction
    X = df[FEATURE_COLS]
    model = load_model(CATBOOST_MODEL_PATH)
    
    # Predict the probability of being the positive class (High Risk = 1)
    probs = model.predict_proba(X)[:, 1]

    # Create a new output DataFrame using only the relevant data
    df_out = df[['firmware_version'] + FEATURE_COLS].copy()
    df_out["risk_score"] = probs
    df_out["high_risk_flag"] = (probs >= RISK_THRESHOLD).astype(int)

    # Save the scored file for logging/audit purposes
    output_csv = f"scored_{os.path.basename(input_csv)}"
    df_out.to_csv(output_csv, index=False)

    summary = {
        "input_file": input_csv,
        "n_high_risk": int((df_out["high_risk_flag"] == 1).sum()),
        "avg_risk_score": float(df_out["risk_score"].mean())
    }

    print(json.dumps(summary, indent=2))

    # --- CI GATE LOGIC ---
    if summary["n_high_risk"] > 0:
        print(f"\n🚨 FAIL: {summary['n_high_risk']} high-risk patch(es) detected. CI BLOCKED.")
        sys.exit(1)
    else:
        print("\n✅ PASS: No high-risk patches detected. CI continues.")
        sys.exit(0)


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
    score_file(input_csv)
