from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, Request, status

from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])

MENU_LINKS = {
    "VETRINA_SHIP_ITA_URL": settings.VETRINA_SHIP_ITA_URL or settings.default_catalog_url,
    "VETRINA_SHIP_SPAGNA_URL": settings.VETRINA_SHIP_SPAGNA_URL or settings.default_catalog_url,
    "VETRINA_REVIEWS_URL": settings.VETRINA_REVIEWS_URL or "https://t.me/+reviews",
    "TELEGRAM_CHANNEL_URL": settings.TELEGRAM_CHANNEL_URL or "https://t.me/+channel",
    "TELEGRAM_CONTACT_URL": settings.TELEGRAM_CONTACT_URL or "https://t.me/username",
    "SIGNAL_CHANNEL_URL": settings.SIGNAL_CHANNEL_URL or "https://signal.group/",
    "SIGNAL_CONTACT_URL": settings.SIGNAL_CONTACT_URL or "https://signal.me/#p/+39",
    "INSTAGRAM_URL": settings.INSTAGRAM_URL or "https://instagram.com/",
    "CATALOG_URL": settings.CATALOG_URL or settings.default_catalog_url,
}

ROOT_MENU = [
    {"label": "🥔 Potato", "target": "potato"},
    {"label": "📨 Telegram", "target": "telegram"},
    {"label": "📡 Signal", "target": "signal"},
    {"label": "📷 Instagram", "target": "instagram"},
    {"label": "🧾 Vetrina", "target": "vetrina"},
]

MENU_CONTENT = {
    "potato": {
        "title": "🥔 Potato",
        "description": "Vetrine ufficiali per spedizioni e recensioni.",
        "items": [
            {"label": "Vetrina Ship ITA", "url": MENU_LINKS["VETRINA_SHIP_ITA_URL"]},
            {"label": "Vetrina Ship Spagna", "url": MENU_LINKS["VETRINA_SHIP_SPAGNA_URL"]},
            {"label": "Canale Recensioni", "url": MENU_LINKS["VETRINA_REVIEWS_URL"]},
        ],
    },
    "telegram": {
        "title": "📨 Telegram",
        "description": "Broadcast ufficiale e contatto diretto.",
        "items": [
            {"label": "Canale Telegram", "url": MENU_LINKS["TELEGRAM_CHANNEL_URL"]},
            {"label": "Contatto Telegram", "url": MENU_LINKS["TELEGRAM_CONTACT_URL"]},
        ],
    },
    "signal": {
        "title": "📡 Signal",
        "description": "Aggiornamenti e ordini su Signal.",
        "items": [
            {"label": "Canale Signal", "url": MENU_LINKS["SIGNAL_CHANNEL_URL"]},
            {"label": "Contatto Ordini", "url": MENU_LINKS["SIGNAL_CONTACT_URL"]},
        ],
    },
    "instagram": {
        "title": "📷 Instagram",
        "description": "Feed ufficiale con drop e teaser.",
        "items": [{"label": "Apri Instagram", "url": MENU_LINKS["INSTAGRAM_URL"]}],
    },
    "vetrina": {
        "title": "🧾 Vetrina",
        "description": "Versione web completa della catalogo experience.",
        "items": [{"label": "Apri WebApp", "web_app": MENU_LINKS["CATALOG_URL"]}],
    },
}


def _display_name(user: dict | None) -> str:
    if not user:
        return "ospite"
    first = user.get("first_name")
    last = user.get("last_name")
    username = user.get("username")
    if first and last:
        return f"{first} {last}"
    return first or username or "ospite"


def _build_keyboard(menu_id: str) -> dict:
    if menu_id == "root":
        return {
            "inline_keyboard": [
                [{"text": item["label"], "callback_data": f"menu:{item['target']}"}] for item in ROOT_MENU
            ]
        }
    submenu = MENU_CONTENT.get(menu_id)
    if not submenu:
        return _build_keyboard("root")
    rows = [
        [
            {"text": entry["label"], "web_app": {"url": entry["web_app"]}}
            if "web_app" in entry
            else {"text": entry["label"], "url": entry["url"]}
        ]
        for entry in submenu["items"]
    ]
    rows.append([{"text": "⬅️ Torna al menu", "callback_data": "menu:root"}])
    return {"inline_keyboard": rows}


def _build_caption(menu_id: str, name: str) -> str:
    if menu_id == "root":
        return f"<b>Benvenuto {name}</b>\nScegli la destinazione dal menu."
    submenu = MENU_CONTENT.get(menu_id)
    if not submenu:
        return _build_caption("root", name)
    return f"<b>{submenu['title']}</b>\n{submenu['description']}"


async def _telegram_request(method: str, payload: dict) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato")
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)
        if response.status_code >= 400:
            logger.error("Telegram API error %s: %s", response.status_code, response.text)
            response.raise_for_status()


async def _send_root_menu(chat_id: int, name: str) -> None:
    logo = settings.PUBLIC_WEBAPP_URL or settings.API_BASE_URL
    logo_url = os.getenv("TELEGRAM_LOGO_URL") or f"{logo.rstrip('/')}/logo.jpg"
    payload = {
        "chat_id": chat_id,
        "caption": _build_caption("root", name),
        "parse_mode": "HTML",
        "reply_markup": _build_keyboard("root"),
    }
    if logo_url:
        payload["photo"] = logo_url
        await _telegram_request("sendPhoto", payload)
    else:
        payload["text"] = payload.pop("caption")
        await _telegram_request("sendMessage", payload)


async def _handle_menu_callback(query: dict) -> None:
    target = query.get("data", "menu:root").split(":", 1)[1]
    name = _display_name(query.get("from"))
    await _telegram_request("answerCallbackQuery", {"callback_query_id": query.get("id")})
    message = query.get("message") or {}
    chat = message.get("chat") or {}
    payload_base = {
        "chat_id": chat.get("id"),
        "message_id": message.get("message_id"),
        "parse_mode": "HTML",
        "reply_markup": _build_keyboard(target),
    }
    if message.get("photo"):
        await _telegram_request(
            "editMessageCaption",
            {**payload_base, "caption": _build_caption(target, name)},
        )
    else:
        await _telegram_request(
            "editMessageText",
            {**payload_base, "text": _build_caption(target, name)},
        )


async def _handle_message(message: dict) -> None:
    text = (message.get("text") or "").strip()
    if not text:
        return
    name = _display_name(message.get("from"))
    if text.startswith("/start") or text.startswith("/menu"):
        await _send_root_menu(message["chat"]["id"], name)
    elif text.startswith("/ping"):
        await _telegram_request("sendMessage", {"chat_id": message["chat"]["id"], "text": "✅ Bot operativo"})


async def _process_update(update: dict) -> None:
    if "message" in update:
        await _handle_message(update["message"])
    elif "callback_query" in update:
        await _handle_menu_callback(update["callback_query"])


@router.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TELEGRAM_BOT_TOKEN mancante")
    if settings.TELEGRAM_WEBHOOK_SECRET:
        provided = request.headers.get("x-telegram-bot-api-secret-token")
        if provided != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Segreto non valido")
    update = await request.json()
    try:
        await _process_update(update)
    except Exception as exc:  # pragma: no cover - vogliamo loggare ma rispondere 200
        logger.exception("Errore nel webhook Telegram: %s", exc)
    return {"ok": True}
