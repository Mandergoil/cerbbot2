# PDR · Telegram WebApp + Admin + Bot

Sistema completo per mostrare un catalogo dark-theme attraverso Telegram WebApp, gestire i prodotti tramite dashboard amministrativa e comandare il flusso tramite bot Telegram.

## Avvio rapido backend (catalogo + admin)

1. Installa le dipendenze Node e prepara l'ambiente:
   ```powershell
   npm install
   cp .env.local .env
   ```
2. Popola il KV con admin e prodotti di esempio (richiede variabili KV + `ADMIN_JWT_SECRET`):
   ```powershell
   npm run bootstrap
   ```
3. Avvia backend + frontend + admin tramite Vercel Dev:
   ```powershell
   npm run dev
   ```
   - Catalogo pubblico: `http://localhost:3000`
   - Dashboard admin: `http://localhost:3000/admin.html`
   - API: `http://localhost:3000/api/*`

## Architettura

| Componente | Stack | Descrizione |
| --- | --- | --- |
| Frontend pubblico (`index.html`) | HTML + CSS + JS | Catalogo tre categorie (Italia, Milano, Spagna), lightbox media, tema nero/rosso. |
| Frontend admin (`admin.html`) | HTML + JS (module) | Login tramite password statica, CRUD prodotti, gestione admin. |
| API (`api/*`) | Serverless Vercel Node | CRUD prodotti + gestione admin + auth JWT firmata. |
| Database | Vercel KV | Hash per prodotti, set per admin, chiavi temporanee token (legacy). |
| Bot (`api/telegram/webhook.js`) | Vercel serverless (Node) | Handler webhook Telegram con menu annidato e WebApp Vetrina. |

```
/
├── index.html                # Vetrina pubblica
├── admin.html                # Dashboard admin (password)
├── style.css                 # Tema condiviso
├── scripts/
│   ├── catalog.js            # Fetch/render prodotti pubblici
│   └── admin.js              # Logica password + CRUD
├── api/
│   ├── products/index.js     # GET/POST prodotti
│   ├── products/[id].js      # GET/PUT/DELETE prodotto
│   ├── admins/index.js       # GET/POST admin
│   ├── admins/[username].js  # DELETE admin
│   ├── auth.js               # Auth password + token legacy
│   └── telegram/webhook.js   # Handler webhook Telegram
├── lib/                      # Utility (KV, auth, body, response)
├── bot/bot.py                # Bot Telegram (debug locale)
├── public/
│   ├── logo.jpg
│   └── uploads/              # Media statici
├── data/seed-products.json   # Esempi prodotti
├── scripts/bootstrap.mjs     # Popola prodotti/admin iniziali
├── package.json              # Dipendenze Node
├── bot/requirements.txt      # Dipendenze bot
└── README.md
```

## Variabili d'ambiente

Duplicare `.env.example` → `.env` e valorizzare:

### Telegram
- `TELEGRAM_BOT_TOKEN` — token BotFather.
- `TELEGRAM_WEBHOOK_URL` — opzionale se usi webhook.
- `TELEGRAM_WEBHOOK_SECRET` — stringa condivisa per verificare il `X-Telegram-Bot-Api-Secret-Token`.
- `TELEGRAM_LOGO_URL` — URL HTTPS dell'immagine da mostrare con `/start` (default al logo deployato su Vercel).
- `SUPER_ADMIN_USERNAME` — @Lapsus00 (o altro super admin).
- `API_BASE_URL`, `PUBLIC_WEBAPP_URL`, `ADMIN_WEBAPP_URL` — URL deployati.
- `ADMIN_STATIC_PASSWORD` — password condivisa per sbloccare la dashboard.

### Link menu
Valorizza tutti gli URL `VETRINA_*`, `TELEGRAM_*`, `SIGNAL_*`, `INSTAGRAM_URL`, `CATALOG_URL` affinché i pulsanti del bot puntino ai canali corretti.

### Backend/Auth
- `ADMIN_JWT_SECRET` — stringa lunga casuale.
- `TOKEN_TTL_MINUTES` — scadenza token monouso.

### KV
- `VERCEL_KV_*` — credenziali dell'istanza KV (automatica su Vercel + KV add-on).

## Setup locale

1. **Installazioni**: Node 18+, npm, Python 3.11+.
2. `npm install` per risolvere le dipendenze JS.
3. `cp .env.example .env` e aggiorna i valori.
4. Popola il KV con admin + prodotti demo:
   ```powershell
   npm run bootstrap
   ```
5. Avvia tutto con Vercel Dev:
   ```powershell
   npx vercel dev
   ```
   - Frontend su `http://localhost:3000`
   - API rispondono su `/api/*`

### Bot Telegram su Vercel (webhook)

1. Assicurati che il deploy su Vercel esponga `https://<dominio>/api/telegram/webhook` e che le variabili `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `API_BASE_URL`, `ADMIN_WEBAPP_URL`, `CATALOG_URL` siano valorizzate in **Production**.
2. Registra il webhook direttamente verso l'endpoint Vercel:
   ```powershell
   $env:BOT_TOKEN="123:ABC"
   $env:WEBHOOK_URL="https://<dominio>/api/telegram/webhook"
   $env:WEBHOOK_SECRET="scegli-una-stringa"
   curl "https://api.telegram.org/bot$env:BOT_TOKEN/setWebhook?url=$env:WEBHOOK_URL&secret_token=$env:WEBHOOK_SECRET"
   ```
3. Telegram inizierà a inviare gli update al serverless: `/start` e `/menu` rispondono con il menu annidato (incluso il pulsante WebApp "Vetrina"), `/ping` verifica lo stato.
4. Per debug locale puoi ancora avviare `bot/bot.py` in polling, ma la produzione resta gestita interamente da Vercel.

## Flusso admin

1. L'amministratore apre `https://dominio/admin.html` e inserisce la password configurata in `ADMIN_STATIC_PASSWORD`.
2. Il frontend chiama `/api/auth` con `intent=password` e riceve un JWT valido `TOKEN_TTL_MINUTES` minuti.
3. Il JWT autorizza tutte le richieste CRUD e la gestione admin.
4. La dashboard consente di:
   - Filtrare prodotti per categoria.
   - Creare/modificare/rimuovere prodotti.
   - Aggiungere o revocare admin (solo super admin identificato nel JWT).

## Endpoint principali

| Metodo | Endpoint | Descrizione | Auth |
| --- | --- | --- | --- |
| GET | `/api/products` | Lista prodotti (`?category=` opzionale) | Pubblico |
| GET | `/api/products/:id` | Dettaglio prodotto | Pubblico |
| POST | `/api/products` | Crea prodotto | JWT admin |
| PUT | `/api/products/:id` | Aggiorna prodotto | JWT admin |
| DELETE | `/api/products/:id` | Elimina prodotto | JWT admin |
| GET | `/api/admins` | Lista admin | JWT admin |
| POST | `/api/admins` | Aggiungi admin | JWT super-admin |
| DELETE | `/api/admins/:username` | Rimuovi admin | JWT super-admin |
| POST | `/api/auth` (intent=password) | Login con password statica → JWT | Password `ADMIN_STATIC_PASSWORD` |
| POST | `/api/auth` (intent=create) | (Legacy) Token monouso | JWT super-admin |
| POST | `/api/auth` (intent=exchange) | (Legacy) Scambia token in JWT | Token monouso |
| GET | `/api/auth` | Chi sono con Bearer | JWT admin |
| POST | `/api/telegram/webhook` | Handler webhook Telegram (/start, menu, WebApp, /ping) | Telegram (secret header) |

## Deploy su Vercel

1. `vercel link` per collegare il progetto.
2. Configura KV add-on e setta le environment variabili da dashboard (Production + Preview).
3. `vercel deploy --prod` per deployare.
4. Imposta `PUBLIC_WEBAPP_URL` e `ADMIN_WEBAPP_URL` con l'URL definitivo.
5. Aggiorna le variabili del bot (`CATALOG_URL`, `VETRINA_*`, `TELEGRAM_*`, `SIGNAL_*`, `TELEGRAM_LOGO_URL`, `TELEGRAM_WEBHOOK_SECRET`).
6. Registra il webhook con `setWebhook` (vedi sezione dedicata) e testa `/start` dal tuo bot.

## Roadmap suggerita
- ✅ Bot Telegram con tastiera e /admin protetto.
- ✅ Frontend responsive dark.
- ✅ Dashboard admin con password statica.
- ✅ API REST con KV + JWT.
- ☐ Endpoint webhook bot (aggiungere `/api/telegram/webhook` se vuoi abilitare webhook su Vercel).
- ☐ Upload media (integrare storage S3/Supabase e salvare URL nei prodotti).

## Testing rapido

- `npm run bootstrap` per avere dati.
- `npx vercel dev` e visita `http://localhost:3000` (catalogo) e `/admin.html` (inserisci la password configurata).
- Avvia il bot, esegui `/start` e verifica immagine + pulsanti.

## Sicurezza

- HTTPS obbligatorio (garantito su Vercel).
- Token JWT firmati lato backend (`ADMIN_JWT_SECRET`).
- Token monouso (legacy) invalidati alla prima lettura (`consumeToken`).
- Admin list gestita su KV; solo super admin può promuovere/revocare.
- Password admin salvata solo lato server via variabile d'ambiente (`ADMIN_STATIC_PASSWORD`).

## Supporto

Per estendere:
- aggiungi categorie direttamente dal KV e aggiornando `FILTERS`/`categories` nei JS.
- integra upload verso storage esterno e salva l'URL nel campo `media`.
- crea un endpoint `/api/telegram/webhook` se preferisci webhook anziché polling.
