from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/banking_db"
    SECRET_KEY: str = "dev-secret-key-change-later"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    OTP_EXPIRE_SECONDS: int = 120
    STARTING_BALANCE: float = 100000.0

    class Config:
        env_file = ".env"


settings = Settings()
