import os
from pydantic import BaseModel
from sqlalchemy.engine import URL


class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "dev").lower()
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DEMO_TOKEN: str | None = os.getenv("DEMO_TOKEN") or None
    ALLOW_INSECURE_DEV_LOGIN: bool = os.getenv("ALLOW_INSECURE_DEV_LOGIN", "false").lower() == "true"

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "geofence")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "geofence")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "geofence")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    @property
    def DATABASE_URL(self) -> str:
        return URL.create(
            "postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    def validate_environment(self) -> None:
        if self.APP_ENV not in {"dev", "test", "staging", "prod"}:
            raise RuntimeError("APP_ENV must be dev, test, staging, or prod")
        if not 1 <= self.ACCESS_TOKEN_EXPIRE_MINUTES <= 1440:
            raise RuntimeError("Invalid token lifetime")
        if self.APP_ENV in {"staging", "prod"}:
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY.lower().startswith(("change", "example")):
                raise RuntimeError("A strong SECRET_KEY is mandatory outside development")
            if len(self.POSTGRES_PASSWORD) < 16 or self.POSTGRES_PASSWORD == "geofence":
                raise RuntimeError("A strong POSTGRES_PASSWORD is mandatory outside development")
            if self.DEMO_TOKEN or self.ALLOW_INSECURE_DEV_LOGIN:
                raise RuntimeError("Development authentication is forbidden outside development")


settings = Settings()
settings.validate_environment()
