from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./banking.db"
    SECRET_KEY: str = "dev-secret-key-change-later-ataf-step9-adaptive"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    OTP_EXPIRE_SECONDS: int = 180
    STARTING_BALANCE: float = 100000.0

    # Policy threshold settings (Step 7 calibration)
    TAU_LOW_MEDIUM: float = 0.30
    TAU_MEDIUM_HIGH: float = 0.70

    class Config:
        env_file = ".env"


settings = Settings()
