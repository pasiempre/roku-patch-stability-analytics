# 🚀 Roku Patch Stability Analytics

## Executive Summary — From Reactive QA to Proactive MLOps

This project delivers a complete, production-ready analytics and MLOps pipeline that **predicts firmware patch regressions before deployment**. It operationalizes ML models into:

- **CI/CD workflows** (automatic deployment blocking)
- **QA resource prioritization**
- **Device-fleet monitoring**
- **Continuous retraining** to prevent model drift

The system transforms firmware QA from reactive investigation to proactive prevention — enabling engineering teams to ship reliable updates while minimizing downstream device failures.

---

## 🏗️ System Architecture Overview

This repository is organized into four tightly integrated layers, corresponding to the real firmware release lifecycle:

```
Data Generation → Feature Engineering → ML Modeling → Production MLOps
```

Each layer strengthens the previous one, ensuring reliability, interpretability, and long-term model performance.

---

## 📁 Project Structure

```
roku-patch-stability-analytics/
├── data/
│   ├── Raw/                    # Raw synthetic telemetry data
│   └── Processed/              # Engineered features & model outputs
├── db/                         # SQLite database
├── models/                     # Trained model artifacts
│   ├── catboost_classifier_v001.cbm
│   ├── catboost_classifier_v002.cbm
│   └── catboost_error_regressor.cbm
├── notebooks/
│   ├── 00_generate_raw_data.ipynb           # Synthetic data generation
│   ├── 01_feature_engineering_sql.ipynb     # SQL-based feature extraction
│   ├── 02_advanced_features.ipynb           # Advanced feature engineering
│   ├── 03_ml_modeling_regressor_classifier.ipynb  # Model training & evaluation
│   ├── 04_qa_prioritization_and_CI_risk_gate_demo.ipynb  # QA prioritization
│   ├── 05_device_monitoring.ipynb           # Device fleet monitoring
│   └── 06_continuous_retraining_pipeline.ipynb    # MLOps retraining
├── src/                        # Python source modules
│   └── config.py               # Centralized configuration
├── sql/                        # SQL scripts
├── reports/                    # Generated reports & figures
├── risk_gate.py                # CI/CD risk scoring script
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 📓 Notebook Pipeline

| # | Notebook | Purpose |
|---|----------|---------|
| 00 | `generate_raw_data` | Generates 1000 synthetic firmware records with realistic correlations |
| 01 | `feature_engineering_sql` | SQL-based feature extraction: error rates, RMA analysis, spike detection |
| 02 | `advanced_features` | Advanced feature engineering and data preparation |
| 03 | `ml_modeling` | CatBoost & RandomForest training with **ROC-AUC: 0.93** |
| 04 | `qa_prioritization` | Risk-based QA workload prioritization |
| 05 | `device_monitoring` | Device fleet monitoring with age-weighted risk |
| 06 | `continuous_retraining` | Drift detection and automated model retraining |

---

## 🤖 Model Performance

| Metric | CatBoost | Random Forest |
|--------|----------|---------------|
| **ROC-AUC** | 0.93 | 0.90 |
| **Accuracy** | 88% | 87% |
| **R² Score** | 0.78 | 0.78 |
| **High Risk Recall** | 68% | 65% |

CatBoost was selected for production use due to its:
- Superior performance with nonlinear feature interactions
- Robustness to sparse/binary features
- Clear feature importance interpretability
- Stability with real-world noise and skew

---

## ▶️ Quick Start

### 1. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Notebooks in Order
Execute notebooks 00-06 sequentially to:
1. Generate synthetic data
2. Engineer features
3. Train models
4. Generate QA priorities
5. Create monitoring dashboards

### 3. Run CI Risk Gate
```bash
python risk_gate.py test_patch_features.csv
```

**Expected output:**
```json
{
  "input_file": "test_patch_features.csv",
  "n_high_risk": 3
}
🚨 FAIL: 3 high-risk patch(es) detected. CI BLOCKED.
```
or:
```
✅ PASS: No high-risk patches detected. CI continues.
```

---

## 🛠️ Technology Stack

| Category | Tools |
|----------|-------|
| **Language** | Python 3.11 |
| **Data Processing** | Pandas, NumPy, SQLAlchemy |
| **Machine Learning** | CatBoost, scikit-learn, XGBoost |
| **Visualization** | Matplotlib, Seaborn |
| **MLOps** | joblib, pathlib |
| **CI Integration** | Python CLI script |

---

## 💡 Why This Project Matters

Companies that ship firmware — TVs, routers, IoT devices, automotive, medical — lose millions annually to patch regressions.

This project demonstrates:
- ✅ **Predictive QA** — Catch regressions before deployment
- ✅ **Real-world CI integration** — Automated deployment gates
- ✅ **Multi-step MLOps workflow** — End-to-end pipeline
- ✅ **Production thinking** — Not just a model, but an operational system

---

## 📄 License

MIT License - See LICENSE file for details.