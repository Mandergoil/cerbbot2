from __future__ import annotations

import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .kv import kv_client
from .repositories import ensure_default_admin
from .routes import admins, auth, products, telegram
from .settings import settings

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Cerbbot2 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(admins.router, prefix="/api")
app.include_router(telegram.router, prefix="/api")


@app.get("/healthz")
async def healthcheck() -> dict:
    return {"ok": True}


@app.on_event("startup")
async def startup_event() -> None:
    await ensure_default_admin()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await kv_client.close()
