from __future__ import annotations

import os
from typing import List


class Settings:
    """Container for environment-aware configuration."""

    def __init__(self) -> None:
        self.KV_REST_API_URL: str | None = os.getenv("KV_REST_API_URL")
        self.KV_REST_API_TOKEN: str | None = os.getenv("KV_REST_API_TOKEN")
        if not self.KV_REST_API_URL or not self.KV_REST_API_TOKEN:
            raise RuntimeError("KV_REST_API_URL e KV_REST_API_TOKEN sono obbligatorie per il backend FastAPI")

        self.ADMIN_JWT_SECRET: str = os.getenv("ADMIN_JWT_SECRET", "dev-secret")
        self.TOKEN_TTL_MINUTES: int = int(os.getenv("TOKEN_TTL_MINUTES", "30"))
        self.SUPER_ADMIN_USERNAME: str = os.getenv("SUPER_ADMIN_USERNAME", "@Lapsus00")
        self.ADMIN_STATIC_PASSWORD: str = os.getenv("ADMIN_STATIC_PASSWORD", "history2552@#")

        self.API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.PUBLIC_WEBAPP_URL: str | None = os.getenv("PUBLIC_WEBAPP_URL")
        self.ADMIN_WEBAPP_URL: str | None = os.getenv("ADMIN_WEBAPP_URL")

        self.CATALOG_URL: str | None = os.getenv("CATALOG_URL")
        self.VETRINA_SHIP_ITA_URL: str | None = os.getenv("VETRINA_SHIP_ITA_URL")
        self.VETRINA_SHIP_SPAGNA_URL: str | None = os.getenv("VETRINA_SHIP_SPAGNA_URL")
        self.VETRINA_REVIEWS_URL: str | None = os.getenv("VETRINA_REVIEWS_URL")
        self.TELEGRAM_CHANNEL_URL: str | None = os.getenv("TELEGRAM_CHANNEL_URL")
        self.TELEGRAM_CONTACT_URL: str | None = os.getenv("TELEGRAM_CONTACT_URL")
        self.SIGNAL_CHANNEL_URL: str | None = os.getenv("SIGNAL_CHANNEL_URL")
        self.SIGNAL_CONTACT_URL: str | None = os.getenv("SIGNAL_CONTACT_URL")
        self.INSTAGRAM_URL: str | None = os.getenv("INSTAGRAM_URL")

        self.TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_WEBHOOK_SECRET: str | None = os.getenv("TELEGRAM_WEBHOOK_SECRET")

        cors_origins = os.getenv("CORS_ALLOW_ORIGINS")
        if cors_origins:
            self.CORS_ALLOW_ORIGINS: List[str] = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        else:
            self.CORS_ALLOW_ORIGINS = ["*"]

    @property
    def default_catalog_url(self) -> str:
        return (
            self.CATALOG_URL
            or self.PUBLIC_WEBAPP_URL
            or self.API_BASE_URL
        )


settings = Settings()
