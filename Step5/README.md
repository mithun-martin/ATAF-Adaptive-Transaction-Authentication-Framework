# Step 5 — Develop the AI Transaction Risk Model

This step trains three machine learning models on the processed IEEE-CIS dataset from Step 4 to predict the probability that a transaction is fraudulent. The output of each model is a **risk score between 0.0 and 1.0** — this score is later used in Step 7 to drive the adaptive security policy.

## Models Trained

| Model | Description |
|---|---|
| **Logistic Regression** | Linear baseline — fast, interpretable, uses `class_weight="balanced"` |
| **Random Forest** | Ensemble of decision trees — handles non-linearity, robust feature importances |
| **XGBoost** | Gradient-boosted trees — highest accuracy candidate, uses `scale_pos_weight` and early stopping on PR-AUC |

## Outputs

After running, the following files are produced:

```
Step5/
├── models/
│   ├── logistic_regression.pkl   ← Trained model (scikit-learn Pipeline)
│   ├── random_forest.pkl         ← Trained model
│   └── xgboost.pkl               ← Trained model
├── outputs/
│   ├── feature_importance_rf.png   ← Top 20 features (Random Forest)
│   ├── feature_importance_xgb.png  ← Top 20 features (XGBoost, by gain)
│   ├── risk_score_distribution.png ← Risk score distributions (fraud vs legit)
│   └── model_summary.txt           ← Quick summary of training results
```

## How to Run

```powershell
# From the Step5 directory
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train_models.py
```

> **Note:** The script reads the processed Parquet files from `../Step4/data/processed/`. Make sure Step 4 has been completed first.

## Next Step

Once training is done, proceed to **Step 6 — Evaluate and Select the AI Model** (`Step6/evaluate_models.py`) which will compare all three models on Precision, Recall, F1, ROC-AUC, PR-AUC and select the best one.
