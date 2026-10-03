from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from models import Account, Beneficiary, Transaction, User  # noqa: F401
from routes.auth import router as auth_router
from routes.account import router as account_router
from routes.beneficiaries import router as beneficiaries_router
from routes.transactions import router as transactions_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Simulated Banking Environment",
    description="Step 1: Basic banking app for adaptive transaction authentication research.",
    version="1.0.0",
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
        "message": "Simulated Banking Environment API (Step 1)",
        "docs": "/docs",
    }
