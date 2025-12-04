from __future__ import annotations

from typing import Any, Dict, List, Optional

from .kv import kv_client
from .settings import settings
from .utils import nano_id, to_hash_map, UPPER_SAFE

PRODUCT_SET = "products"
ADMIN_SET = "admins"
TOKEN_PREFIX = "admin-tokens"


async def list_products(category: Optional[str] = None) -> List[Dict[str, Any]]:
    ids = await kv_client.command("SMEMBERS", PRODUCT_SET) or []
    items = []
    for pid in ids:
        product = await get_product(pid)
        if not product:
            continue
        if category and product["category"] != category:
            continue
        items.append(product)
    return items


async def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    raw = await kv_client.command("HGETALL", f"{PRODUCT_SET}:{product_id}")
    if not raw:
        return None
    data = to_hash_map(raw)
    return {
        "id": product_id,
        "name": data.get("name", ""),
        "category": data.get("category", ""),
        "media": data.get("media", ""),
        "description": data.get("description", ""),
        "featured": data.get("featured", "false") == "true"
    }


async def save_product(payload: Dict[str, Any]) -> Dict[str, Any]:
    product_id = payload.get("id") or nano_id()
    featured = payload.get("featured", False)
    await kv_client.command("SADD", PRODUCT_SET, product_id)
    await kv_client.command(
        "HSET",
        f"{PRODUCT_SET}:{product_id}",
        "name",
        payload["name"],
        "category",
        payload["category"],
        "media",
        payload["media"],
        "description",
        payload["description"],
        "featured",
        "true" if featured else "false",
    )
    return await get_product(product_id) or payload


async def delete_product(product_id: str) -> None:
    await kv_client.command("SREM", PRODUCT_SET, product_id)
    await kv_client.command("DEL", f"{PRODUCT_SET}:{product_id}")


async def list_admins() -> List[str]:
    return await kv_client.command("SMEMBERS", ADMIN_SET) or []


async def add_admin(username: str) -> List[str]:
    await kv_client.command("SADD", ADMIN_SET, username)
    return await list_admins()


async def remove_admin(username: str) -> List[str]:
    await kv_client.command("SREM", ADMIN_SET, username)
    return await list_admins()


async def is_admin(username: str) -> bool:
    admins = await list_admins()
    return username in admins


async def ensure_default_admin() -> None:
    admins = await list_admins()
    if settings.SUPER_ADMIN_USERNAME not in admins:
        await add_admin(settings.SUPER_ADMIN_USERNAME)


async def put_token(token: str, username: str, ttl_seconds: int) -> None:
    await kv_client.command(
        "SET",
        f"{TOKEN_PREFIX}:{token}",
        username,
        "EX",
        ttl_seconds,
    )


async def consume_token(token: str) -> Optional[str]:
    key = f"{TOKEN_PREFIX}:{token}"
    owner = await kv_client.command("GET", key)
    if owner:
        await kv_client.command("DEL", key)
    return owner


async def generate_magic_token() -> str:
    token = nano_id(12, alphabet=UPPER_SAFE)
    return token
