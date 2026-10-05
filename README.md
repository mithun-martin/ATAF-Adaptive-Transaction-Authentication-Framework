# ATAF — Adaptive Transaction Authentication Framework

ATAF is an AI-assisted adaptive transaction authentication framework designed to protect banking users from social-engineering-based financial fraud by dynamically detecting suspicious transactions and applying stronger, transaction-bound verification only when necessary.

---

## Systems Compared in this Project

| System | Authentication Pipeline | Security Mechanism | Usability / Burden | Status |
|---|---|---|---|---|
| **System 1: Baseline** | $\text{Password} \to \text{OTP} \to \text{Transaction}$ | Conventional 2FA (Knowledge + Possession) | Low friction; vulnerable to social engineering / vishing | **Completed (Step 2)** ✅ |
| **System 2: Static 3FA** | $\text{Password} \to \text{OTP} \to \text{Additional Verification} \to \text{Transaction}$ | Static 3FA: 100% of transactions require transaction-bound confirmation & PIN | Maximum security; highest cognitive burden on user | **Completed (Step 3)** ✅ |
| **System 3: Proposed (Adaptive)** | $\text{Password} \to \text{OTP} \to \text{AI Risk Assessment} \to \text{Adaptive Verification} \to \text{Transaction}$ | AI Risk Engine dynamically triggers additional verification only for high-risk transactions | Optimal security-usability trade-off | *Steps 4–9* |

---

## Repository Structure

Each step of the ATAF project plan is housed in its own self-contained, fully working directory:

* **[Step 1 — Simulated Banking Environment](./Step1/)** (Responsible: Aritra)
  * Portable zero-config SQLite backend (FastAPI) and modern React frontend (Vite, Tailwind CSS).
  * User registration/login, account balances, beneficiaries, money transfer, and login OTP simulation.

* **[Step 2 — Implement Baseline Authentication (System 1)](./Step2/)** (Responsible: Aditya)
  * Implements the conventional 2FA transaction pipeline:
    $$\text{Password} \longrightarrow \text{OTP} \longrightarrow \text{Transaction}$$
  * Password authorization requirement before dispatching transaction OTP.
  * Ephemeral transaction challenge management with attempt limiting and TTL expiry.
  * Verified end-to-end with automated test suite (`test_baseline_flow.py`).

* **[Step 3 — Implement Static 3FA (System 2)](./Step3/)** (Responsible: Aditya)
  * Implements the static three-factor authentication pipeline enforced on 100% of transactions:
    $$\text{Password} \longrightarrow \text{OTP} \longrightarrow \text{Additional Confirmation} \longrightarrow \text{Transaction}$$
  * Cryptographic transaction binding: HMAC-SHA256 mathematical seal binding recipient account, amount, nonce, and challenge session.
  * Explicit transaction-bound affirmations and 4-digit Transaction Security PIN verification.
  * Verified end-to-end with automated test suite (`test_static_3fa_flow.py`).

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

---

## Next Steps (Team Handoff)

* **Step 4 — Collect and Prepare the Dataset (Aritra):**
  Collect financial fraud dataset (e.g. PaySim), handle class imbalance (SMOTE), feature engineering, train/test split.
* **Step 5 — Develop the AI Transaction Risk Model (Mithun):**
  Train Logistic Regression, Random Forest, and XGBoost models to output probability risk scores (0.0 to 1.0).
* **Step 6 — Evaluate and Select the AI Model (Aritra):**
  Precision, Recall, F1, PR-AUC, ROC-AUC evaluation.
* **Step 7 & 8 — Design Adaptive Security Policy & Cryptographic Verification (Mithun + Aditya):**
  Dynamic risk tiers (Low $\to$ Normal, Medium $\to$ Warning, High $\to$ Strong Verification).
* **Step 9 — Integrate Proposed System (All)**
* **Step 10 — Create Social-Engineering Attack Scenarios (Aditya)**
* **Step 11 & 12 — Experimental Comparison & Usability Evaluation (All / Mithun + Aditya)**
