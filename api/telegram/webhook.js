import { parseJsonBody } from "../../lib/body.js";
import { json, methodNotAllowed, badRequest, unauthorized } from "../../lib/response.js";

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const API_BASE = process.env.API_BASE_URL || "https://thehistoryfarmbot.vercel.app";
const ADMIN_SERVICE_BEARER = process.env.ADMIN_SERVICE_BEARER;
const SUPER_ADMIN = process.env.SUPER_ADMIN_USERNAME || "@Lapsus00";
const LOGO_URL = process.env.TELEGRAM_LOGO_URL || `${process.env.PUBLIC_WEBAPP_URL || API_BASE}/logo.jpg`;
const TELEGRAM_SECRET = process.env.TELEGRAM_WEBHOOK_SECRET;

const MENU_LINKS = {
  VETRINA_SHIP_ITA_URL: process.env.VETRINA_SHIP_ITA_URL || process.env.CATALOG_URL || API_BASE,
  VETRINA_SHIP_SPAGNA_URL: process.env.VETRINA_SHIP_SPAGNA_URL || process.env.CATALOG_URL || API_BASE,
  VETRINA_REVIEWS_URL: process.env.VETRINA_REVIEWS_URL || "https://t.me/+reviews",
  TELEGRAM_CHANNEL_URL: process.env.TELEGRAM_CHANNEL_URL || "https://t.me/+channel",
  TELEGRAM_CONTACT_URL: process.env.TELEGRAM_CONTACT_URL || "https://t.me/username",
  SIGNAL_CHANNEL_URL: process.env.SIGNAL_CHANNEL_URL || "https://signal.group/",
  SIGNAL_CONTACT_URL: process.env.SIGNAL_CONTACT_URL || "https://signal.me/#p/+39",
  INSTAGRAM_URL: process.env.INSTAGRAM_URL || "https://instagram.com/",
  CATALOG_URL: process.env.CATALOG_URL || API_BASE
};

const ROOT_MENU = [
  { label: "🥔 Potato", target: "potato" },
  { label: "📨 Telegram", target: "telegram" },
  { label: "📡 Signal", target: "signal" },
  { label: "📷 Instagram", target: "instagram" },
  { label: "🧾 Vetrina", target: "vetrina" }
];

const MENU_CONTENT = {
  potato: {
    title: "🥔 Potato",
    description: "Vetrine ufficiali per spedizioni e recensioni.",
    items: [
      { label: "Vetrina Ship ITA", url: MENU_LINKS.VETRINA_SHIP_ITA_URL },
      { label: "Vetrina Ship Spagna", url: MENU_LINKS.VETRINA_SHIP_SPAGNA_URL },
      { label: "Canale Recensioni", url: MENU_LINKS.VETRINA_REVIEWS_URL }
    ]
  },
  telegram: {
    title: "📨 Telegram",
    description: "Broadcast ufficiale e contatto diretto.",
    items: [
      { label: "Canale Telegram", url: MENU_LINKS.TELEGRAM_CHANNEL_URL },
      { label: "Contatto Telegram", url: MENU_LINKS.TELEGRAM_CONTACT_URL }
    ]
  },
  signal: {
    title: "📡 Signal",
    description: "Aggiornamenti e ordini su Signal.",
    items: [
      { label: "Canale Signal", url: MENU_LINKS.SIGNAL_CHANNEL_URL },
      { label: "Contatto Ordini", url: MENU_LINKS.SIGNAL_CONTACT_URL }
    ]
  },
  instagram: {
    title: "📷 Instagram",
    description: "Feed ufficiale con drop e teaser.",
    items: [{ label: "Apri Instagram", url: MENU_LINKS.INSTAGRAM_URL }]
  },
  vetrina: {
    title: "🧾 Vetrina",
    description: "Versione web completa della catalogo experience.",
    items: [{ label: "Apri WebApp", url: MENU_LINKS.CATALOG_URL }]
  }
};

const TELEGRAM_API = TOKEN ? `https://api.telegram.org/bot${TOKEN}` : null;

function displayName(user) {
  if (!user) return "ospite";
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  }
  return user.first_name || user.username || "ospite";
}

async function telegramRequest(method, payload) {
  if (!TELEGRAM_API) {
    throw new Error("TELEGRAM_BOT_TOKEN non configurato");
  }
  const res = await fetch(`${TELEGRAM_API}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Telegram API error ${res.status}: ${text}`);
  }
  return res.json();
}

function buildKeyboard(menuId) {
  if (menuId === "root") {
    return {
      inline_keyboard: ROOT_MENU.map((item) => [
        { text: item.label, callback_data: `menu:${item.target}` }
      ])
    };
  }
  const submenu = MENU_CONTENT[menuId];
  if (!submenu) {
    return buildKeyboard("root");
  }
  const rows = submenu.items.map((entry) => [{ text: entry.label, url: entry.url }]);
  rows.push([{ text: "⬅️ Torna al menu", callback_data: "menu:root" }]);
  return { inline_keyboard: rows };
}

function buildCaption(menuId, name) {
  if (menuId === "root") {
    return `<b>Benvenuto ${name}</b>\nScegli la destinazione dal menu.`;
  }
  const submenu = MENU_CONTENT[menuId];
  if (!submenu) {
    return buildCaption("root", name);
  }
  return `<b>${submenu.title}</b>\n${submenu.description}`;
}

async function sendRootMenu(chatId, name) {
  if (LOGO_URL) {
    await telegramRequest("sendPhoto", {
      chat_id: chatId,
      photo: LOGO_URL,
      caption: buildCaption("root", name),
      parse_mode: "HTML",
      reply_markup: buildKeyboard("root")
    });
    return;
  }
  await telegramRequest("sendMessage", {
    chat_id: chatId,
    text: buildCaption("root", name),
    parse_mode: "HTML",
    reply_markup: buildKeyboard("root")
  });
}

async function handleMenuCallback(query) {
  const target = query.data?.split(":", 2)[1] || "root";
  const name = displayName(query.from);
  await telegramRequest("answerCallbackQuery", { callback_query_id: query.id });
  if (!query.message?.chat) return;
  const payloadBase = {
    chat_id: query.message.chat.id,
    message_id: query.message.message_id,
    parse_mode: "HTML",
    reply_markup: buildKeyboard(target)
  };
  if (query.message.photo?.length) {
    await telegramRequest("editMessageCaption", {
      ...payloadBase,
      caption: buildCaption(target, name)
    });
  } else {
    await telegramRequest("editMessageText", {
      ...payloadBase,
      text: buildCaption(target, name)
    });
  }
}

async function callBackend(path, { method = "GET", body } = {}) {
  if (!ADMIN_SERVICE_BEARER) {
    throw new Error("ADMIN_SERVICE_BEARER non impostato");
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${ADMIN_SERVICE_BEARER}`,
      "Content-Type": "application/json"
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Backend error ${res.status}: ${text}`);
  }
  return res.json();
}

async function handleAdminCommand(message) {
  const user = message.from;
  const username = user?.username ? `@${user.username}` : null;
  if (!username) {
    await telegramRequest("sendMessage", {
      chat_id: message.chat.id,
      text: "Serve un username pubblico per accedere all'area admin."
    });
    return;
  }
  const admins = await callBackend("/api/admins");
  const allowed = admins.admins || [];
  if (username !== SUPER_ADMIN && !allowed.includes(username)) {
    await telegramRequest("sendMessage", {
      chat_id: message.chat.id,
      text: "Non sei autorizzato ad accedere all'area admin."
    });
    return;
  }
  const tokenData = await callBackend("/api/auth", {
    method: "POST",
    body: { intent: "create", username }
  });
  const link = `${process.env.ADMIN_WEBAPP_URL || `${API_BASE}/admin.html`}?token=${tokenData.token}`;
  await telegramRequest("sendMessage", {
    chat_id: message.chat.id,
    text: `Link valido ${tokenData.expiresInMinutes} minuti:\n${link}`,
    disable_web_page_preview: true
  });
}

async function handleMessage(message) {
  if (!message?.text) return;
  const text = message.text.trim();
  const name = displayName(message.from);
  if (text.startsWith("/start") || text.startsWith("/menu")) {
    await sendRootMenu(message.chat.id, name);
    return;
  }
  if (text.startsWith("/admin")) {
    await handleAdminCommand(message);
    return;
  }
  if (text.startsWith("/ping")) {
    await telegramRequest("sendMessage", { chat_id: message.chat.id, text: "✅ Bot operativo" });
  }
}

async function processUpdate(update) {
  if (update.message) {
    await handleMessage(update.message);
    return;
  }
  if (update.callback_query) {
    await handleMenuCallback(update.callback_query);
    return;
  }
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    methodNotAllowed(res, ["POST"]);
    return;
  }
  if (!TOKEN) {
    badRequest(res, "TELEGRAM_BOT_TOKEN non configurato");
    return;
  }
  if (TELEGRAM_SECRET) {
    const secret = req.headers["x-telegram-bot-api-secret-token"];
    if (secret !== TELEGRAM_SECRET) {
      unauthorized(res);
      return;
    }
  }
  let update;
  try {
    update = await parseJsonBody(req);
  } catch (error) {
    badRequest(res, error.message);
    return;
  }
  try {
    await processUpdate(update);
    json(res, 200, { ok: true });
  } catch (error) {
    console.error("Telegram handler error", error);
    json(res, 200, { ok: true });
  }
}
