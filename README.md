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

* **[Step 8 — Implement Transaction-Bound Verification](./Step8/)** (Responsible: Aditya) ✅
  * Cryptographic dynamic linking complying with PSD2 Article 97 and NIST SP 800-63B.
  * Formats high-risk confirmation challenge matching ATAF specification:
    $$\text{HMAC-SHA256}(K_{\text{system}}, \text{challenge\_id} \mathbin{\Vert} \text{sender} \mathbin{\Vert} \text{beneficiary} \mathbin{\Vert} \text{amount} \mathbin{\Vert} \text{currency} \mathbin{\Vert} \text{timestamp} \mathbin{\Vert} \text{nonce})$$
  * Anti-tampering protection: detects and rejects amount inflation, account redirection, and replay attacks.
  * Verified with 100% passing unit tests (`test_transaction_binding.py`).

* **[Step 9 — Integrate the Proposed System (System 3)](./Step9/)** (Responsible: All) ✅
  * Complete proposed end-to-end adaptive banking system (System 3) unifying Steps 1 through 8.
  * Adaptive authentication pipeline:
    $$\text{Banking App} \longrightarrow \text{Password + OTP} \longrightarrow \text{Transaction} \longrightarrow \text{AI Risk Engine} \longrightarrow \text{Risk Score} \longrightarrow \text{Adaptive Security Policy} \longrightarrow \text{Additional Verification (if needed)} \longrightarrow \text{Authorization}$$
  * Dynamically evaluates transaction risk via trained XGBoost model and contextual behavioural heuristics.
  * Calibrated tri-tier policy:
    - **LOW RISK ($R < 0.30$):** Frictionless 2FA (Password + OTP).
    - **MEDIUM RISK ($0.30 \le R < 0.70$):** Anti-Social-Engineering Advisory Warning Banner + OTP.
    - **HIGH RISK ($R \ge 0.70$):** Step-Up 3FA (PSD2 Art. 97 HMAC-SHA256 Transaction-Bound Seal + Affirmations + 4-digit PIN).
  * Interactive React + Tailwind CSS dashboard and FastAPI backend verified with automated integration test suite (`test_adaptive_system.py`).

* **[Step 10 — Create Social-Engineering Attack Scenarios](./Step10/)** (Responsible: Aditya) ✅
  * Defined standardized catalog of 6 social-engineering attack patterns and 2 benign usability control scenarios:
    - `SCN-01`: Classic OTP Voice Phishing / Vishing (Bank Impersonation)
    - `SCN-02`: New Beneficiary + Large Emergency Transfer (Family Impersonation)
    - `SCN-03`: Remote Access Tool Takeover (AnyDesk / TeamViewer Screen-Sharing)
    - `SCN-04`: Off-Hours Coercion ("Digital Arrest" Extortion at 02:45 AM)
    - `SCN-05`: Extreme Volume Anomaly (Crypto / Ponzi Yield Investment Scam)
    - `SCN-06`: Compound Multi-Indicator Takeover (Credential Stuffing + Velocity Burst + Night Transfer)
    - `SCN-07` & `SCN-08`: Benign Grocery and Monthly Rent Control Baselines
  * Multi-system simulation harness (`attack_simulator.py`) proving:
    - **System 1 (Baseline 2FA):** 0% fraud defense (100% compromise rate on social engineering).
    - **System 2 (Static 3FA):** 100% fraud defense, but imposes high friction (3.0 steps) on 100% of benign transfers.
    - **System 3 (Proposed Adaptive):** 100% fraud defense with optimal low friction (2.0 steps) on benign transfers.
  * Verified with interactive demo (`demo_attack_scenarios.py`) and pytest suite (`test_attack_scenarios.py`).

* **[Step 11 — Run Experimental Comparison](./Step11/)** (Responsible: All) ✅
  * Rigorous empirical comparison of Baseline (System 1), Static 3FA (System 2), and Proposed Adaptive (System 3) across both the 88,581 IEEE-CIS test transactions and the social-engineering attack scenario set.
  * Security benchmarks:
    - **Attack Success Rate (ASR):** System 1 = 100.0% (Vulnerable) vs. System 2 = 0.0% vs. System 3 = **0.0%** (Protected).
    - **Fraud Detection Rate (FDR):** System 1 = 0.0% vs. System 2 = 100.0% vs. System 3 = **100.0%**.
    - **Large-Scale ROC-AUC:** 0.5000 (S1/S2) vs. **0.9468** (S3).
    - **Large-Scale PR-AUC:** 0.0350 (S1/S2) vs. **0.6926** (S3).
    - **False Acceptance Rate (FAR):** System 1 = 1.0000 vs. System 2 = 0.0000 vs. System 3 = **0.0929**.
  * Usability & Authentication Burden:
    - **Mean Transaction Time:** System 1 = 17.0s vs. System 2 = 32.2s (+89.4% penalty) vs. System 3 = **18.1s (Saves 14.1s per transfer!)**.
    - **Step-Up Frequency:** System 1 = 0.0% vs. System 2 = 100.0% vs. System 3 = **4.78% (Targeted step-up)**.
  * Generated 4 publication-quality plots: Pareto Frontier (`security_vs_burden.png`), Grouped Bar Chart (`metrics_comparison_barchart.png`), Scenario Breakdown (`attack_defense_comparison.png`), and Threshold Sensitivity Curve (`friction_tradeoff_curve.png`).
  * Automated test suite (`test_experimental_comparison.py`) passing 3/3 tests.

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

* **Step 12 — Usability Evaluation (Mithun + Aditya):**
  Conduct structured human-centered usability evaluation (System Usability Scale [SUS], User Burden Scale [UBS], NASA-TLX cognitive workload, completion times) across the interfaces of all three systems.
* **Step 13 — Research Analysis & IEEE Paper (All)**
