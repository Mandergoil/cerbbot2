from __future__ import annotations

import secrets
import string
from typing import Iterable, List


ALPHANUMERIC = string.ascii_lowercase + string.digits
UPPER_SAFE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def nano_id(length: int = 8, alphabet: str = ALPHANUMERIC) -> str:
    """Generate a short pseudo-random identifier."""
    return "".join(secrets.choice(alphabet) for _ in range(length))


def to_hash_map(items: Iterable[str]) -> dict[str, str]:
    """Convert Upstash HGETALL result (flat list) into a dictionary."""
    items_list: List[str] = list(items)
    return {
        items_list[i]: items_list[i + 1]
        for i in range(0, len(items_list), 2)
        if i + 1 < len(items_list)
    }
