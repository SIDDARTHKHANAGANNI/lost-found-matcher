from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    upload_dir: str = "uploads"

    # rate limiting — all configurable via .env, not hardcoded
    rate_limit_auth_per_ip: str = "5/minute"
    rate_limit_auth_per_account: str = "5/minute"
    rate_limit_public: str = "60/minute"
    rate_limit_authenticated: str = "120/minute"
    rate_limit_backoff_base_seconds: int = 30

    class Config:
        env_file = ".env"

settings = Settings()