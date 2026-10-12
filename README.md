# ATAF — Adaptive Transaction Authentication Framework

ATAF is an AI-assisted adaptive transaction authentication framework designed to protect banking users from social-engineering-based financial fraud by dynamically detecting suspicious transactions and applying stronger, transaction-bound verification only when necessary.

---

## Systems Compared in this Project

| System | Authentication Pipeline | Security Mechanism | Usability / Burden | Status |
|---|---|---|---|---|
| **System 1: Baseline** | $\text{Password} \to \text{OTP} \to \text{Transaction}$ | Conventional 2FA (Knowledge + Possession) | Low friction; vulnerable to social engineering / vishing | **Completed (Step 2)** ✅ |
| **System 2: Static 3FA** | $\text{Password} \to \text{OTP} \to \text{Additional Verification} \to \text{Transaction}$ | Static 3FA: 100% of transactions require transaction-bound confirmation & PIN | Maximum security; highest cognitive burden on user | **Completed (Step 3)** ✅ |
| **System 3: Proposed (Adaptive)** | $\text{Password} \to \text{OTP} \to \text{AI Risk Assessment} \to \text{Adaptive Verification} \to \text{Transaction}$ | AI Risk Engine dynamically triggers additional verification only for high-risk transactions | Optimal security-usability trade-off | **In Progress (Steps 4–9)** 🚀 |

---

## Repository Structure

Each step of the ATAF project plan is housed in its own self-contained, fully working directory:

* **[Step 1 — Simulated Banking Environment](./Step1/)** (Responsible: Aritra) ✅
  * Portable zero-config SQLite backend (FastAPI) and modern React frontend (Vite, Tailwind CSS).
  * User registration/login, account balances, beneficiaries, money transfer, and login OTP simulation.

* **[Step 2 — Implement Baseline Authentication (System 1)](./Step2/)** (Responsible: Aditya) ✅
  * Implements the conventional 2FA transaction pipeline:
    $$\text{Password} \longrightarrow \text{OTP} \longrightarrow \text{Transaction}$$
  * Password authorization requirement before dispatching transaction OTP.
  * Ephemeral transaction challenge management with attempt limiting and TTL expiry.
  * Verified end-to-end with automated test suite (`test_baseline_flow.py`).

* **[Step 3 — Implement Static 3FA (System 2)](./Step3/)** (Responsible: Aditya) ✅
  * Implements the static three-factor authentication pipeline enforced on 100% of transactions:
    $$\text{Password} \longrightarrow \text{OTP} \longrightarrow \text{Additional Confirmation} \longrightarrow \text{Transaction}$$
  * Cryptographic transaction binding: HMAC-SHA256 mathematical seal binding recipient account, amount, nonce, and challenge session.
  * Explicit transaction-bound affirmations and 4-digit Transaction Security PIN verification.
  * Verified end-to-end with automated test suite (`test_static_3fa_flow.py`).

* **[Step 4 — Collect and Prepare the Dataset](./Step4/)** (Responsible: Aritra) ✅
  * Automated data engineering pipeline on the **IEEE-CIS Fraud Detection** dataset (590k+ transactions).
  * Memory optimization (70%+ RAM reduction), missing-value imputation, label encoding.
  * Stratified 70/15/15 train/validation/test split.
  * Class-imbalance handling: Combined `RandomUnderSampler` + `RandomOverSampler` applied strictly to training data (producing 188,032 balanced training samples).
  * Exported to compressed Parquet files (`train_processed.parquet`, `val_processed.parquet`, `test_processed.parquet`).

* **[Step 5 — Develop the AI Transaction Risk Model](./Step5/)** (Responsible: Mithun) ✅
  * Trained three candidate machine learning models for transaction risk scoring:
    1. **Logistic Regression** (baseline linear model with `StandardScaler` and balanced weighting)
    2. **Random Forest** (ensemble tree classifier with 300 estimators, max depth 12)
    3. **XGBoost** (gradient-boosted trees with scale positive weighting and PR-AUC early stopping)
  * Feature importance analyses and probability risk score distribution visualizations saved.
  * Serialized models saved to `Step5/models/`.

* **[Step 6 — Evaluate and Select the AI Model](./Step6/)** (Responsible: Aritra) ✅
  * Evaluated all three models against the held-out test set (88,581 transactions, 3.5% fraud rate).
  * Comprehensive metrics: Precision, Recall, F1, ROC-AUC, PR-AUC, FPR, FNR.
  * Generated ROC curves, PR curves, confusion matrix heatmaps, and threshold analysis curves.
  * **Selected Model: XGBoost** (ROC-AUC: **0.9468**, PR-AUC: **0.6926**, Fraud Recall: **82.45%**, FPR: **7.34%**).

* **[Step 7 — Design the Adaptive Security Policy](./Step7/)** (Responsible: Mithun + Aditya) ✅
  * Tri-tier adaptive risk policy engine mapping continuous risk scores $R \in [0.0, 1.0]$ into dynamic authentication tiers:
    - **LOW RISK ($R < 0.30$):** Normal 2FA (Password + OTP) for low user friction.
    - **MEDIUM RISK ($0.30 \le R < 0.70$):** Anti-Social-Engineering Advisory Warning Banner + OTP.
    - **HIGH RISK ($R \ge 0.70$):** Strong 3FA (Transaction-bound HMAC-SHA256 seal + Security PIN).
  * Fail-secure fallback architecture and 100% unit-tested decision engine.

---

## Model Evaluation Leaderboard (Step 6)

| Model | Precision | Recall (TPR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR | Selection |
|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** | 0.1346 | 0.7215 | 0.2269 | 0.8559 | 0.4042 | 0.1681 | 0.2785 | Baseline |
| **Random Forest** | 0.1893 | 0.7512 | 0.3024 | 0.8950 | 0.5499 | 0.1166 | 0.2488 | Candidate |
| **XGBoost** | **0.2894** | **0.8245** | **0.4284** | **0.9468** | **0.6926** | **0.0734** | **0.1755** | **Selected Winner 🏆** |

---

## Quick Start Guide

### Step 2: Baseline Authentication (System 1)
```bash
# 1. Backend
cd Step2/backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python test_baseline_flow.py   # Run automated test suite
python run.py                  # API runs at http://127.0.0.1:8000

# 2. Frontend (new terminal)
cd Step2/frontend
npm install
npm run dev                    # UI runs at http://localhost:5173
```

### Step 3: Static 3FA (System 2)
```bash
# 1. Backend
cd Step3/backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python test_static_3fa_flow.py # Run automated test suite
python run.py                  # API runs at http://127.0.0.1:8000

# 2. Frontend (new terminal)
cd Step3/frontend
npm install
npm run dev                    # UI runs at http://localhost:5173
```

### Steps 4, 5 & 6: AI Data Prep, Training & Evaluation
```bash
# Step 4: Prepare dataset
cd Step4
python prepare_dataset.py

# Step 5: Train models
cd ../Step5
python train_models.py

# Step 6: Evaluate and select model
cd ../Step6
python evaluate_models.py
```

---

## Next Steps (Project Roadmap)

* **Step 8 — Implement Transaction-Bound Verification (Aditya):**
  Formalize transaction-bound verification mechanism with explicit confirmation questions and HMAC-SHA256 parameter binding seals for high-risk transfers.
* **Step 9 — Integrate the Proposed System (All):**
  Full adaptive end-to-end banking pipeline (System 3) connecting the banking app (Step 1), policy engine (Step 7), and transaction binding (Step 8).
* **Step 10 — Create Social-Engineering Attack Scenarios (Aditya)**
* **Step 11 — Run Experimental Comparison (All)**
* **Step 12 — Usability Evaluation (Mithun + Aditya)**
* **Step 13 — Research Analysis & IEEE Paper (All)**
