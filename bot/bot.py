import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CATALOG_URL = os.getenv("CATALOG_URL", "https://example.com")
LOGO_CANDIDATES = [
  Path(__file__).resolve().parent.parent / "logo.jpg",
  Path(__file__).resolve().parent.parent / "public" / "logo.jpg"
]
LOGO_PATH = next((path for path in LOGO_CANDIDATES if path.exists()), None)

MENU_LINKS = {
  "VETRINA_SHIP_ITA_URL": os.getenv("VETRINA_SHIP_ITA_URL", CATALOG_URL),
  "VETRINA_SHIP_SPAGNA_URL": os.getenv("VETRINA_SHIP_SPAGNA_URL", CATALOG_URL),
  "VETRINA_REVIEWS_URL": os.getenv("VETRINA_REVIEWS_URL", "https://t.me/+reviews"),
  "TELEGRAM_CHANNEL_URL": os.getenv("TELEGRAM_CHANNEL_URL", "https://t.me/+channel"),
  "TELEGRAM_CONTACT_URL": os.getenv("TELEGRAM_CONTACT_URL", "https://t.me/username"),
  "SIGNAL_CHANNEL_URL": os.getenv("SIGNAL_CHANNEL_URL", "https://signal.group/"),
  "SIGNAL_CONTACT_URL": os.getenv("SIGNAL_CONTACT_URL", "https://signal.me/#p/+39"),
  "INSTAGRAM_URL": os.getenv("INSTAGRAM_URL", "https://instagram.com/"),
  "CATALOG_URL": CATALOG_URL
}

ROOT_MENU = [
  {"label": "🥔 Potato", "target": "potato"},
  {"label": "📨 Telegram", "target": "telegram"},
  {"label": "📡 Signal", "target": "signal"},
  {"label": "📷 Instagram", "target": "instagram"},
  {"label": "🧾 Vetrina", "target": "vetrina"}
]

MENU_CONTENT = {
  "potato": {
    "title": "🥔 Potato",
    "description": "Vetrine ufficiali per spedizioni e recensioni.",
    "items": [
      {"label": "Vetrina Ship ITA", "url": MENU_LINKS["VETRINA_SHIP_ITA_URL"]},
      {"label": "Vetrina Ship Spagna", "url": MENU_LINKS["VETRINA_SHIP_SPAGNA_URL"]},
      {"label": "Canale Recensioni", "url": MENU_LINKS["VETRINA_REVIEWS_URL"]}
    ]
  },
  "telegram": {
    "title": "📨 Telegram",
    "description": "Canale broadcast e contatto diretto.",
    "items": [
      {"label": "Canale Telegram", "url": MENU_LINKS["TELEGRAM_CHANNEL_URL"]},
      {"label": "Contatto Telegram", "url": MENU_LINKS["TELEGRAM_CONTACT_URL"]}
    ]
  },
  "signal": {
    "title": "📡 Signal",
    "description": "Canale Signal e contatto ordini.",
    "items": [
      {"label": "Canale Signal", "url": MENU_LINKS["SIGNAL_CHANNEL_URL"]},
      {"label": "Contatto Ordini", "url": MENU_LINKS["SIGNAL_CONTACT_URL"]}
    ]
  },
  "instagram": {
    "title": "📷 Instagram",
    "description": "Feed ufficiale con drop e teaser.",
    "items": [
      {"label": "Apri Instagram", "url": MENU_LINKS["INSTAGRAM_URL"]}
    ]
  },
  "vetrina": {
    "title": "🧾 Vetrina",
    "description": "Versione web completa della catalogo experience.",
    "items": [
      {"label": "Apri WebApp", "web_app": MENU_LINKS["CATALOG_URL"]}
    ]
  }
}

def build_keyboard(menu_id: str, user_name: str) -> InlineKeyboardMarkup:
  if menu_id == "root":
    rows = []
    for item in ROOT_MENU:
      rows.append([InlineKeyboardButton(item["label"], callback_data=f"menu:{item['target']}")])
    return InlineKeyboardMarkup(rows)
  submenu = MENU_CONTENT.get(menu_id)
  if not submenu:
    return build_keyboard("root", user_name)
  rows = []
  for entry in submenu["items"]:
    if entry.get("web_app"):
      rows.append([
        InlineKeyboardButton(entry["label"], web_app=WebAppInfo(url=entry["web_app"]))
      ])
    else:
      rows.append([
        InlineKeyboardButton(entry["label"], url=entry["url"])
      ])
  rows.append([InlineKeyboardButton("⬅️ Torna al menu", callback_data="menu:root")])
  return InlineKeyboardMarkup(rows)

def build_caption(menu_id: str, user_name: str) -> str:
  if menu_id == "root":
    return f"<b>Benvenuto {user_name}</b>\nScegli la destinazione dal menu."
  submenu = MENU_CONTENT.get(menu_id)
  if not submenu:
    return build_caption("root", user_name)
  return f"<b>{submenu['title']}</b>\n{submenu['description']}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  name = user.first_name or user.full_name or "ospite"
  caption = build_caption("root", name)
  keyboard = build_keyboard("root", name)
  target = update.message or update.effective_message
  if LOGO_PATH and update.message:
    with open(LOGO_PATH, "rb") as photo:
      await update.message.reply_photo(photo, caption=caption, reply_markup=keyboard, parse_mode=ParseMode.HTML)
  else:
    await target.reply_text(caption, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  target = query.data.split(":", 1)[1] if ":" in query.data else "root"
  user = update.effective_user
  name = user.first_name or user.full_name or "ospite"
  caption = build_caption(target, name)
  keyboard = build_keyboard(target, name)
  if query.message.photo:
    await query.edit_message_caption(caption=caption, reply_markup=keyboard, parse_mode=ParseMode.HTML)
  else:
    await query.edit_message_text(text=caption, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("✅ Bot operativo")

def main():
  if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN non configurato")
  application = Application.builder().token(TOKEN).build()
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CommandHandler("menu", start))
  application.add_handler(CommandHandler("ping", health))
  application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern=r"^menu:"))
  logger.info("Bot avviato. In ascolto...")
  application.run_polling()

if __name__ == "__main__":
  main()
