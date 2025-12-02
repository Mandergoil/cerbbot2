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
| Frontend admin (`admin.html`) | HTML + JS (module) | Login tramite token monouso, CRUD prodotti, gestione admin. |
| API (`api/*`) | Serverless Vercel Node | CRUD prodotti + gestione admin + auth/token su KV. |
| Database | Vercel KV | Hash per prodotti, set per admin, chiavi temporanee token. |
| Bot (`api/telegram/webhook.js`) | Vercel serverless (Node) | Handler webhook Telegram con menu annidato, /admin token, senza VPS. |

```
/
├── index.html                # Vetrina pubblica
├── admin.html                # Dashboard admin (token)
├── style.css                 # Tema condiviso
├── scripts/
│   ├── catalog.js            # Fetch/render prodotti pubblici
│   └── admin.js              # Logica token + CRUD
├── api/
│   ├── products/index.js     # GET/POST prodotti
│   ├── products/[id].js      # GET/PUT/DELETE prodotto
│   ├── admins/index.js       # GET/POST admin
│   ├── admins/[username].js  # DELETE admin
│   ├── auth.js               # Token (create/exchange/impersonate)
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

### Link menu
Valorizza tutti gli URL `VETRINA_*`, `TELEGRAM_*`, `SIGNAL_*`, `INSTAGRAM_URL`, `CATALOG_URL` affinché i pulsanti del bot puntino ai canali corretti.

### Backend/Auth
- `ADMIN_JWT_SECRET` — stringa lunga casuale.
- `TOKEN_TTL_MINUTES` — scadenza token monouso.
- `ADMIN_SERVICE_BEARER` — JWT del super admin usato dal bot per chiamare le API. Puoi generarlo con `node -e "import('./lib/auth.js').then(({generateAdminToken})=>console.log(generateAdminToken({username: '@Lapsus00'})))"` dopo aver configurato le variabili.

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

1. Assicurati che il deploy su Vercel esponga `https://<dominio>/api/telegram/webhook` e che le variabili `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `ADMIN_SERVICE_BEARER`, `API_BASE_URL`, `ADMIN_WEBAPP_URL` siano valorizzate in **Production**.
2. Registra il webhook direttamente verso l'endpoint Vercel:
   ```powershell
   $env:BOT_TOKEN="123:ABC"
   $env:WEBHOOK_URL="https://<dominio>/api/telegram/webhook"
   $env:WEBHOOK_SECRET="scegli-una-stringa"
   curl "https://api.telegram.org/bot$env:BOT_TOKEN/setWebhook?url=$env:WEBHOOK_URL&secret_token=$env:WEBHOOK_SECRET"
   ```
3. Telegram inizierà a inviare gli update al serverless: `/start` e `/menu` risponderanno con il menu annidato, `/admin` genera il link monouso via API.
4. Per debug locale puoi ancora avviare `bot/bot.py` in polling, ma la produzione resta gestita interamente da Vercel.

## Flusso admin

1. Super admin (`/admin` sul bot) riceve token monouso (`POST /api/auth intent=create`).
2. Bot invia link `https://dominio/admin.html?token=XYZ`.
3. Admin.html chiama `/api/auth` intent `exchange` e riceve JWT per tutte le chiamate CRUD.
4. Dashboard permette:
   - Filtrare prodotti per categoria.
   - Creare/modificare/rimuovere prodotti.
   - Aggiungere admin (solo super admin) e revocare utenti.

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
| POST | `/api/auth` (intent=create) | Token monouso | JWT super-admin |
| POST | `/api/auth` (intent=exchange) | Scambia token in JWT | Nessuno (usa token) |
| GET | `/api/auth` | Chi sono con Bearer | JWT admin |
| POST | `/api/telegram/webhook` | Handler webhook Telegram (/start, menu, /admin) | Telegram (secret header) |

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
- ✅ Dashboard admin con token monouso.
- ✅ API REST con KV + JWT.
- ☐ Endpoint webhook bot (aggiungere `/api/telegram/webhook` se vuoi abilitare webhook su Vercel).
- ☐ Upload media (integrare storage S3/Supabase e salvare URL nei prodotti).

## Testing rapido

- `npm run bootstrap` per avere dati.
- `npx vercel dev` e visita `http://localhost:3000` (catalogo) e `/admin.html` (usa `?token=` generato).
- Avvia il bot, esegui `/start` e verifica immagine + pulsanti.

## Sicurezza

- HTTPS obbligatorio (garantito su Vercel).
- Token JWT firmati lato backend (`ADMIN_JWT_SECRET`).
- Token monouso invalidati alla prima lettura (`consumeToken`).
- Admin list gestita su KV; solo super admin può promuovere/revocare.
- Bot usa `ADMIN_SERVICE_BEARER` dedicato; rigenera periodicamente.

## Supporto

Per estendere:
- aggiungi categorie direttamente dal KV e aggiornando `FILTERS`/`categories` nei JS.
- integra upload verso storage esterno e salva l'URL nel campo `media`.
- crea un endpoint `/api/telegram/webhook` se preferisci webhook anziché polling.
