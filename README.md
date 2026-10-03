# ATAF — Adaptive Transaction Authentication Framework

## Project Goal
Develop an AI-assisted adaptive transaction authentication system that protects users from social-engineering-based financial fraud by detecting suspicious transactions and applying stronger verification only when necessary.

The project compares three systems:
1. **Baseline:** Password → OTP → Transaction
2. **Static 3FA:** Password → OTP → Additional Verification → Transaction
3. **Proposed:** Password → OTP → AI Risk Assessment → Adaptive Verification → Transaction

---

## Current Status: Step 1 Completed ✅
The foundational **Simulated Banking Environment** has been fully built. 

**Recent Architecture Updates:**
* **Zero-Config Database:** Migrated from PostgreSQL to **SQLite**. No database server setup is required.
* **OTP Simulation:** Phone numbers are now captured during registration. The backend generates OTPs, which are simulated on the UI for testing purposes.
* **Banking Realism:** Added IFSC codes, transaction remarks, and unique reference IDs.
* **Profile Integration:** Added a user profile interface and masked sensitive information.

### Tech Stack
* **Backend:** Python, FastAPI, SQLAlchemy, SQLite, Pydantic
* **Frontend:** React, TypeScript, Vite, Tailwind CSS

---

## Local Setup Instructions

### 1. Start the Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```
* API runs at: `http://127.0.0.1:8000`
* Swagger Docs: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend
Open a new terminal:
```powershell
cd frontend
npm install
npm run dev
```
* App runs at: `http://localhost:5173`

---

## Next Steps (Team Handoff)

### Aditya — Steps 2 & 3 (Cybersecurity / Authentication)
* **Goal:** Implement the Baseline and Static 3FA transaction flows.
* **Action:** Create a new feature branch. Modify the `Transfer.tsx` frontend page and the `transactions.py` backend route to enforce OTP verification (Step 2) and an additional confirmation (Step 3) *before the transaction is finalized*. 
* **Tip:** Implement a configuration toggle (`AUTH_MODE = "baseline" | "static_3fa" | "adaptive"`) in the backend to switch between authentication modes easily for later experiments.

### Aritra — Step 4 (Data Engineering)
* **Goal:** Collect and prepare the financial fraud dataset.
* **Action:** Create a new `ai/` or `data-pipeline/` folder. Download a public dataset (e.g., PaySim from Kaggle) and create Jupyter Notebooks (`.ipynb`) to clean data, encode categorical features, handle class imbalances (e.g., using SMOTE), and perform train/validation/test splits.

### Mithun — Step 5 (AI/ML)
* **Goal:** Develop the AI Transaction Risk Model.
* **Action:** Prepare the machine learning architecture using `scikit-learn` and `xgboost`. Set up training pipelines for Logistic Regression, Random Forest, and XGBoost models to output a probability risk score (0.0 to 1.0) based on Aritra's processed dataset.
