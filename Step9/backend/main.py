from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from models import Account, Beneficiary, Transaction, User, OTP, TransactionChallenge  # noqa: F401
from routes.auth import router as auth_router
from routes.account import router as account_router
from routes.beneficiaries import router as beneficiaries_router
from routes.transactions import router as transactions_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ATAF — System 3: Proposed Adaptive Authentication",
    description=(
        "Adaptive Transaction Authentication Framework — Step 9.\n\n"
        "Proposed System 3 — Adaptive Multi-Factor Authentication Architecture:\n"
        "Password → AI Risk Engine (XGBoost) → Adaptive Security Policy:\n"
        "  • LOW RISK (<0.30): Streamlined 2FA (Password + OTP)\n"
        "  • MEDIUM RISK (0.30-0.70): Contextual Anti-Social-Engineering Warning + OTP\n"
        "  • HIGH RISK (>=0.70): Transaction-Bound Step-Up (Affirmations + HMAC-SHA256 Seal + PIN)\n\n"
        "Compliant with PSD2 RTS Article 97 and NIST SP 800-63B."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(beneficiaries_router)
app.include_router(transactions_router)


@app.get("/")
def root():
    return {
        "application": "ATAF — System 3: Proposed Adaptive Authentication",
        "step": 9,
        "auth_flow": "Password -> AI Risk Engine -> Adaptive Policy -> (OTP / Warning / Transaction-Bound 3FA)",
        "features": [
            "Factor 1: Account Password Authentication",
            "AI Inference Engine: Step 5 XGBoost Tabular Classifier & Contextual Heuristics",
            "Adaptive Security Policy: Low (<0.30), Medium (0.30-0.70), High (>=0.70)",
            "Factor 2: Out-of-band Dynamic OTP",
            "Factor 3 (High-Risk Step-Up): PSD2 Art. 97 HMAC-SHA256 Transaction Binding + PIN",
            "Zero-Config SQLite Portable Database",
        ],
        "database": "SQLite (portable, zero-config)",
        "docs": "/docs",
        "status": "running",
    }
