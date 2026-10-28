from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock Market Prediction API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super_secret_key_change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    DATABASE_URL: str = "postgresql://admin:adminpassword@localhost:5432/stock_db"

    class Config:
        env_file = ".env"

settings = Settings()
