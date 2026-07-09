from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "ModelTrace")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    environment: str = os.getenv("ENVIRONMENT", "development")

    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    field_encryption_key: str = os.getenv("FIELD_ENCRYPTION_KEY", "").strip()
    pii_hash_key: str = os.getenv("PII_HASH_KEY", "").strip()
    password_pepper: str = os.getenv("PASSWORD_PEPPER", "").strip()
    api_key_hash_secret: str = os.getenv("API_KEY_HASH_SECRET", "").strip()
    password_iterations: int = int(os.getenv("PASSWORD_ITERATIONS", "390000"))
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "120"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
    cookie_secure: bool = _bool_env("COOKIE_SECURE", "false")
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax")
    public_app_url: str = os.getenv("PUBLIC_APP_URL", "http://127.0.0.1:3000").rstrip("/")

    mongodb_url: str = os.getenv("MONGODB_URL", "").strip()
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "modeltrace")
    local_store_path: str = os.getenv(
        "LOCAL_STORE_PATH",
        str(Path(__file__).resolve().parents[2] / ".data" / "modeltrace.json"),
    )
    upload_dir: str = os.getenv(
        "UPLOAD_DIR",
        str(Path(__file__).resolve().parents[2] / ".data" / "uploads"),
    )
    max_avatar_bytes: int = int(os.getenv("MAX_AVATAR_BYTES", "2097152"))

    smtp_host: str = os.getenv("SMTP_HOST", "").strip()
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password: str = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from: str = os.getenv("SMTP_FROM", "ModelTrace <no-reply@modeltrace.local>").strip()
    smtp_starttls: bool = _bool_env("SMTP_STARTTLS", "true")
    email_verification_minutes: int = int(os.getenv("EMAIL_VERIFICATION_MINUTES", "1440"))
    password_reset_minutes: int = int(os.getenv("PASSWORD_RESET_MINUTES", "45"))

    redis_url: str = os.getenv("REDIS_URL", "").strip()
    enable_security_headers: bool = _bool_env("ENABLE_SECURITY_HEADERS", "true")
    cors_origins: list[str] = None  # type: ignore[assignment]
    allowed_hosts: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "cors_origins",
            _csv_env("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"),
        )
        object.__setattr__(
            self,
            "allowed_hosts",
            _csv_env("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"),
        )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"prod", "production"}

    @property
    def uses_default_secret(self) -> bool:
        return self.secret_key == "change-me-in-production"


settings = Settings()
