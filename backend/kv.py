from __future__ import annotations

import asyncio
from typing import Any, Iterable, Sequence

import httpx

from .settings import settings


class KVClient:
    """Minimal Upstash KV REST client."""

    def __init__(self) -> None:
        self._base_url = settings.KV_REST_API_URL.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.KV_REST_API_TOKEN}"}
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def _ensure_client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._client is None:
                self._client = httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=10)
            return self._client

    async def command(self, *parts: Sequence[Any]) -> Any:
        client = await self._ensure_client()
        response = await client.post("/", json=list(parts))
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        return payload.get("result")

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


kv_client = KVClient()
