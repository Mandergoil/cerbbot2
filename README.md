# PDR · FastAPI + Telegram + Vetrina

Stack completo per mostrare il catalogo tramite WebApp Telegram e gestire il backend con **FastAPI**. Il frontend resta una pagina statica (index/admin/script/style), mentre tutte le API `/api/*` sono ora in Python.

## Avvio rapido

1. Crea l'ambiente Python (PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
2. Duplica le variabili (`copy .env.example .env` se esiste, altrimenti crea `.env` con i valori attuali: Upstash KV, segreti JWT, token Telegram).
3. Popola Upstash KV con admin + prodotti demo:
   ```powershell
   python -m backend.bootstrap
   ```
4. Avvia il backend FastAPI su porta 8000:
   ```powershell
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Servi i file statici con qualunque web server (anche `python -m http.server 3000`). Se backend e statici stanno sullo stesso dominio, il frontend continua a parlare con `/api/*` senza modifiche.

> VPS Ubuntu? Installare `python3-venv`, creare la virtualenv, `pip install -r backend/requirements.txt`, eseguire `python -m backend.bootstrap`, poi avviare `pm2 start "uvicorn backend.main:app --host 0.0.0.0 --port 8000" --name cerbbot` e mettere Nginx davanti.

## Architettura

| Componente | Stack | Descrizione |
| --- | --- | --- |
| Frontend pubblico (`index.html`) | HTML + CSS + JS | Catalogo con filtri categorie (Italia, Milano, Spagna) + lightbox. |
| Frontend admin (`admin.html`) | HTML + JS modules | Dashboard con password, CRUD prodotti e gestione admin. |
| API (`backend/main.py`) | FastAPI + httpx | Endpoint `/api/products`, `/api/admins`, `/api/auth`, `/api/telegram/webhook`. |
| Database | Upstash / Vercel KV | Hash prodotti, set admin, chiavi token monouso. |
| Bot (`backend/routes/telegram.py`) | FastAPI + Telegram Bot API | Menu annidato, pulsante WebApp, comandi `/start`, `/menu`, `/ping`. |

```
/
├── index.html                # Vetrina pubblica
├── admin.html                # Dashboard admin
├── style.css
├── scripts/
│   ├── catalog.js            # Frontend pubblico
│   └── admin.js              # CRUD + auth admin
├── backend/
│   ├── main.py               # App FastAPI
│   ├── settings.py           # Config/Env
│   ├── kv.py                 # Client Upstash
│   ├── repositories.py       # Prodotti/Admin/Token
│   ├── security.py           # JWT + auth dependencies
│   ├── routes/
│   │   ├── products.py
│   │   ├── admins.py
│   │   ├── auth.py
│   │   └── telegram.py
│   ├── models.py             # Schemi Pydantic
│   ├── utils.py              # Helper comuni
│   └── bootstrap.py          # Seed iniziale
├── data/seed-products.json   # Prodotti demo
├── public/
│   ├── logo.jpg
│   └── uploads/
├── bot/bot.py                # Bot polling/debug
├── backend/requirements.txt  # Dipendenze FastAPI
└── README.md
```

## Variabili d'ambiente

Creare `.env` (usato da FastAPI e bootstrap) con:

### Backend/Auth
- `ADMIN_STATIC_PASSWORD` → password da digitare su `admin.html`.
- `ADMIN_JWT_SECRET` → stringa lunga per firmare i JWT.
- `TOKEN_TTL_MINUTES` → durata token monouso.
- `SUPER_ADMIN_USERNAME` → utente autorizzato a promuovere altri admin.

### Upstash KV
- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`

### Telegram e link
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_LOGO_URL`
- `API_BASE_URL`, `PUBLIC_WEBAPP_URL`, `ADMIN_WEBAPP_URL`
- Tutti i link del menu: `VETRINA_*`, `TELEGRAM_*`, `SIGNAL_*`, `INSTAGRAM_URL`, `CATALOG_URL`.

## Setup locale dettagliato

1. Installare Python 3.11+.
2. Seguire i passi dell'Avvio rapido.
3. Avviare un server statico per `index.html`/`admin.html` (Live Server, nginx, ecc.).
4. Se il backend gira su host/porta diversa, aggiornare `API_BASE_URL` in `scripts/admin.js`.
5. Testare login admin → CRUD prodotti → gestione admin.

## Webhook Telegram

1. Esporre FastAPI via HTTPS (`https://dominio/api/telegram/webhook`).
2. Registrare il webhook:
   ```powershell
   $env:BOT_TOKEN="123:ABC"
   $env:WEBHOOK_URL="https://dominio/api/telegram/webhook"
   $env:WEBHOOK_SECRET="stringa"
   curl "https://api.telegram.org/bot$env:BOT_TOKEN/setWebhook?url=$env:WEBHOOK_URL&secret_token=$env:WEBHOOK_SECRET"
   ```
3. Verificare `/start`, `/menu`, `/ping` dal bot.
4. Per test locali usare `python -m bot.bot` (polling).

## Endpoint principali

| Metodo | Endpoint | Descrizione | Auth |
| --- | --- | --- | --- |
| GET | `/api/products` | Lista prodotti (`?category=`) | Pubblico |
| GET | `/api/products/{id}` | Dettaglio prodotto | Pubblico |
| POST | `/api/products` | Crea prodotto | JWT admin |
| PUT | `/api/products/{id}` | Aggiorna prodotto | JWT admin |
| DELETE | `/api/products/{id}` | Elimina prodotto | JWT admin |
| GET | `/api/admins` | Lista admin | JWT admin |
| POST | `/api/admins` | Aggiungi admin | JWT super admin |
| DELETE | `/api/admins/{username}` | Rimuovi admin | JWT super admin |
| POST | `/api/auth` (`intent=password`) | Login password → JWT | Password admin |
| POST | `/api/auth` (`intent=create`) | Token monouso | JWT super admin |
| POST | `/api/auth` (`intent=exchange`) | Token → JWT | Token valido |
| GET | `/api/auth` | Profilo admin | JWT admin |
| POST | `/api/telegram/webhook` | Handler Telegram | Header segreto |

## Deploy su VPS

1. Copiare il repo su `/var/www/cerbbot2`.
2. `python -m venv .venv && source .venv/bin/activate` (oppure PowerShell su Windows).
3. `pip install -r backend/requirements.txt`.
4. Compilare `.env` e lanciare `python -m backend.bootstrap`.
5. Avviare Uvicorn con PM2/systemd sulla porta 8000.
6. Nginx come reverse proxy + HTTPS (Certbot), servendo i file statici con `root /var/www/cerbbot2`.
7. Aggiornare il webhook Telegram verso `https://dominio/api/telegram/webhook`.

## Testing rapido

- `python -m backend.bootstrap` → dati fittizi.
- `uvicorn backend.main:app --reload` → API locali.
- Chiamate via curl/Postman o direttamente dalla dashboard.
- Bot: `python -m bot.bot` (polling) per testare i comandi.

## Sicurezza

- HTTPS obbligatorio in produzione.
- JWT firmati con `ADMIN_JWT_SECRET`.
- Token monouso invalidati alla prima lettura.
- Solo il super admin può promuovere/rimuovere altri admin.
- Password admin mantenuta lato server (`ADMIN_STATIC_PASSWORD`).

## Roadmap

- ✅ Migrazione FastAPI completata.
- ✅ Webhook Telegram gestito da FastAPI.
- ☐ Upload media (S3/Supabase) con gestione URL.
- ☐ Deploy automatizzato (Ansible/Terraform).

## Supporto

Apri una issue o scrivimi su Telegram se vuoi estendere la piattaforma (nuove categorie, upload media, notifiche push, ecc.).
