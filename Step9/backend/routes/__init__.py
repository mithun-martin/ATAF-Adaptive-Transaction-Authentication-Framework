from routes.auth import router as auth_router
from routes.account import router as account_router
from routes.beneficiaries import router as beneficiaries_router
from routes.transactions import router as transactions_router

__all__ = [
    "auth_router",
    "account_router",
    "beneficiaries_router",
    "transactions_router",
]
