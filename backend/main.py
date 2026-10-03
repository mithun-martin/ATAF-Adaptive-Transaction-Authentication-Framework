from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from models import Account, Beneficiary, Transaction, User, OTP  # noqa: F401
from routes.auth import router as auth_router
from routes.account import router as account_router
from routes.beneficiaries import router as beneficiaries_router
from routes.transactions import router as transactions_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ATAF — Simulated Banking Environment",
    description=(
        "Adaptive Transaction Authentication Framework — Step 1.\n\n"
        "A simulated banking application for testing authentication systems.\n"
        "Uses SQLite for portability — no database server required."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
        "application": "ATAF — Simulated Banking Environment",
        "version": "2.0.0",
        "database": "SQLite (portable, zero-config)",
        "docs": "/docs",
        "status": "running",
    }
