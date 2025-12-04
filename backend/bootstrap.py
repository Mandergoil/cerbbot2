from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from .repositories import ensure_default_admin, save_product

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "seed-products.json"


async def seed_products() -> None:
    if not DATA_FILE.exists():
        print("Nessun file seed trovato, salto i prodotti")
        return
    items = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for item in items:
        await save_product(item)
        print(f"✓ Seeded {item['id']}")


async def main() -> None:
    await ensure_default_admin()
    await seed_products()
    print("Bootstrap completo")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
