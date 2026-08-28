import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "catalogo-api")
    app_env: str = os.getenv("APP_ENV", "development")
    port: int = int(os.getenv("PORT", "8000"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./catalogo.db")
    r2_endpoint: str = os.getenv("R2_ENDPOINT", "")
    r2_region: str = os.getenv("R2_REGION", "auto")
    r2_access_key_id: str = os.getenv("R2_ACCESS_KEY_ID", "")
    r2_secret_access_key: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    r2_bucket: str = os.getenv("R2_BUCKET", "")
    r2_public_url: str = os.getenv("R2_PUBLIC_URL", "")
    backend_url: str = os.getenv("BACKEND_URL", "")
    frontend_url: str = os.getenv("FRONTEND_URL", "")


settings = Settings()
