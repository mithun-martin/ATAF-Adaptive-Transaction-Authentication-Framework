# Step 6 — Evaluate and Select the AI Model

This step evaluates the three models trained in Step 5 on the held-out **test set** (88,581 transactions, 3.5% fraud rate) from the IEEE-CIS dataset.

## Evaluation Results

| Model | Precision | Recall (TPR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR |
|---|---|---|---|---|---|---|---|
| **Logistic Regression** | 0.1346 | 0.7215 | 0.2269 | 0.8559 | 0.4042 | 0.1681 | 0.2785 |
| **Random Forest** | 0.1893 | 0.7512 | 0.3024 | 0.8950 | 0.5499 | 0.1166 | 0.2488 |
| **XGBoost (Winner 🏆)** | **0.2894** | **0.8245** | **0.4284** | **0.9468** | **0.6926** | **0.0734** | **0.1755** |

### Selected Model: **XGBoost**
- **ROC-AUC: 0.9468**
- **PR-AUC: 0.6926** (Primary evaluation metric for class-imbalanced fraud detection)
- **Fraud Recall: 82.45%** (Detects over 82% of all fraudulent transactions)
- **Lowest FPR: 7.34%** (Minimizes false alarms for legitimate users)

## Outputs Generated

All plots and tables are located in `Step6/outputs/`:
- `metrics_table.csv` — Comprehensive metric comparison table
- `roc_curves.png` — ROC curve comparison plot
- `pr_curves.png` — Precision-Recall curve comparison plot
- `confusion_matrices.png` — Side-by-side confusion matrices
- `metrics_comparison.png` — Bar chart across all key metrics
- `threshold_analysis.png` — Precision, Recall, F1, and FPR curve across thresholds for XGBoost
- `evaluation_report.txt` — Full text evaluation summary
- `best_model.txt` — Identifies XGBoost for automatic downstream ingestion in Step 7

## How to Run
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python evaluate_models.py
```
