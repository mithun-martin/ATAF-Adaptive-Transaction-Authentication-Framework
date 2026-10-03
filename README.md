# ATAF — Adaptive Transaction Authentication Framework

This repository contains the Step 1 implementation of the project: a working simulated banking environment used to test and compare three authentication designs:

1. Baseline: Password → OTP → Transaction
2. Static 3FA: Password → OTP → Extra Verification → Transaction
3. Proposed adaptive system: Password → OTP → AI Risk Assessment → Adaptive Verification → Transaction

## Current status

This branch includes Step 1 only: the simulated banking app and transactional flow. The later security and AI stages are not yet implemented here.

## What Step 1 includes

- User registration and login
- Account dashboard with balance view
- Beneficiary management
- Money transfer flow
- Transaction history
- OTP-style confirmation interface within the banking workflow

## Tech stack

| Layer | Stack |
|-------|-------|
| Backend | Python, FastAPI, SQLAlchemy, PostgreSQL, Pydantic |
| Frontend | React, Vite, TypeScript |

## Project structure

- backend/ — FastAPI API, models, routes, schemas, and transaction logic
- frontend/ — React app for login, dashboard, transfers, beneficiaries, and transaction history

## Local setup

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

## Database configuration

Example backend environment variables:

```env
DATABASE_URL=postgresql://banking:banking@localhost:5432/banking_db
SECRET_KEY=dev-secret-key-change-later
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Step 1 flow

Register → Login → Dashboard → Add Beneficiary → Transfer Funds → View Balance → Record Transactions

This step deliberately focuses on the banking domain and transaction workflow so the next team member can add security layers without reworking the core app logic.

## What is not included yet

- Baseline OTP-only auth enforcement
- Static 3FA check on every transaction
- AI fraud/risk scoring
- Adaptive verification policy
- Transaction-bound confirmation mechanism
- Attack scenarios and evaluation

## Handoff for Step 2

The next contributor should continue from this codebase by implementing the Baseline Authentication system:

- Username/password login
- OTP verification after login
- Transaction approval flow under the baseline model
- No AI or dynamic checks yet

The banking application and API foundation are already in place, so Step 2 should focus on authentication logic and transaction gating rather than rebuilding the app itself.

## Repository status

This repository is now synced with the GitHub remote and contains the completed Step 1 setup ready for continuation.
