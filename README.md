# ATAF — Step 1: Simulated Banking Environment

Part of [ATAF — Adaptive Transaction Authentication Framework](https://github.com/mithun-martin/ATAF-Adaptive-Transaction-Authentication-Framework).

**This repository / folder currently contains ONLY Step 1.**

Later steps (baseline auth, static 3FA, AI risk model, adaptive policy, attack scenarios, evaluation, IEEE paper) are **not** implemented here.

## What Step 1 includes

- User registration / login (JWT)
- Account dashboard + balance (starting balance ₹1,00,000)
- Beneficiary management (add / view / delete)
- Money transfer with confirmation
- Transaction history (COMPLETED / FAILED)

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python, FastAPI, SQLAlchemy, PostgreSQL, Pydantic |
| Frontend | React, Vite, TypeScript, Tailwind CSS |

## PostgreSQL

`	ext
database: banking_db
user:     banking
password: banking
`

Copy ackend/.env.example to ackend/.env and adjust if needed:

`	ext
DATABASE_URL=postgresql://banking:banking@localhost:5432/banking_db
SECRET_KEY=dev-secret-key-change-later
ACCESS_TOKEN_EXPIRE_MINUTES=60
`

## Run backend

`powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
`

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Run frontend

`powershell
cd frontend
npm install
npm run dev
`

Open: http://localhost:5173

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Register + create bank account |
| POST | /auth/login | Login (JWT) |
| GET | /account | Own account + balance |
| GET/POST | /beneficiaries | List / add beneficiaries |
| DELETE | /beneficiaries/{id} | Delete beneficiary |
| GET/POST | /transactions | History / transfer |

## Flow

`	ext
Register → Login → Dashboard
  → Add Beneficiary → Send Money → Confirm
  → Balance check → Deduct → Record → History
`

Transaction logic is separated in ackend/services/transaction_service.py so later authentication steps can wrap transfers without rewriting the banking core.

## Not in this step

- Baseline OTP auth / Static 3FA
- AI risk scoring / fraud detection
- Adaptive authentication
- Transaction-bound crypto verification
- Attack scenarios / experimental evaluation
