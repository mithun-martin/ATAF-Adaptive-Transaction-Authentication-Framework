from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import random
import string

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(plain_pin: str, hashed_pin: str | None) -> bool:
    # If no pin explicitly set yet, default fallback is "1234"
    if not hashed_pin:
        return plain_pin == "1234"
    return pwd_context.verify(plain_pin, hashed_pin)


def generate_nonce(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def generate_transaction_seal(
    challenge_id: str,
    user_id: int,
    account_num: str,
    amount: float,
    nonce: str,
) -> str:
    """
    Cryptographically bind transaction details using HMAC-SHA256.
    Ensures authorization is mathematically tied to recipient, amount, nonce, and challenge session.
    """
    msg = f"{challenge_id}:{user_id}:{account_num}:{amount:.2f}:{nonce}"
    return hmac.new(settings.SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = int(user_id)
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


get_verified_user = get_current_user


def generate_account_number() -> str:
    """Generate a realistic 10-digit bank account number."""
    return f"{random.randint(1000000000, 9999999999)}"


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    return "".join(random.choices(string.digits, k=length))
