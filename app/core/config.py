import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DEMO_TOKEN: str | None = os.getenv("DEMO_TOKEN")

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "geofence")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "geofence")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "geofence")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

