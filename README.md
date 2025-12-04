# The History Farm · Telegram Bot

Repository minimale: contiene il bot Telegram in Python **e** una WebApp Flask (`server.py` + `index.html` + `admin.html`) pronta da collegare al dominio `the-history-farm.top` o da pubblicare su qualsiasi VPS/hosting con Python 3.

## Struttura
```
/
├── bot/
│   ├── bot.py               # Entry point Telegram
│   └── requirements.txt     # python-telegram-bot + dotenv + Flask
├── server.py                # backend Flask (API + static pages)
├── data/
│   └── products.json        # archivio prodotti (1 demo per categoria)
├── logo.jpg                 # opzionale per inviare /start con immagine
├── .env.example             # variabili da copiare in .env
├── index.html               # vetrina mobile-first (Telegram WebApp ready)
├── admin.html               # pannello admin connesso al backend
└── README.md
```

## Setup locale
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r bot/requirements.txt
copy .env.example .env  # compila i valori reali
python -m bot.bot
```

## WebApp Flask (index + admin + API)
La vetrina è ottimizzata per Telegram WebApp con layout nero/rosso minimale (logo, tre categorie, ricerca). L'area admin comunica con il backend Python per creare/modificare/eliminare prodotti e salvare tutto su `data/products.json` (di default un solo prodotto demo per Italia, Milano, Spagna).

### Avvio rapido in locale
```powershell
# dalla root del repo
python -m venv .venv
.\.venv\Scripts\activate
pip install -r bot/requirements.txt
python server.py  # espone API + index + admin su http://localhost:8000
```
Apri `http://localhost:8000/` per la vetrina e `http://localhost:8000/admin` per l'area gestionale.

### Endpoint principali
- `GET /api/products` → lista prodotti correnti.
- `POST /api/products` → crea prodotto (`name`, `description`, `category`, `mediaUrl` opzionale).
- `PUT /api/products/<id>` → aggiorna i campi forniti.
- `DELETE /api/products/<id>` → elimina l'elemento.
- `POST /api/products/reset` → ripristina i tre demo.

### Feature
- **UI essenziale**: logo `logo.jpg` in header, tre pill per categoria, ricerca live, 1 card demo per categoria.
- **Stile coerente**: palette nero/rosso, tipografia Space Grotesk, compatibile Telegram WebApp (`Telegram.WebApp.ready`).
- **Admin con backend**: CRUD completo, filtro di lista, reset demo, export JSON (clipboard), gestione di `mediaUrl`.
- **Persistenza file**: i dati restano in `data/products.json`, così puoi versionare o fare backup facile.

### Collegamento dominio (NameSilo)
1. Deploya `server.py` (es. su VPS Ubuntu, Railway, Render) con Python 3.10+ e `pip install -r bot/requirements.txt`.
2. Configura un reverse proxy (Nginx/Caddy) che punti all'app Flask (porta 8000 o quella scelta) e abilita HTTPS.
3. Su NameSilo crea un record A verso l'IP del proxy oppure un CNAME verso il tuo provider.
4. Aggiorna la variabile `CATALOG_URL` nel bot con `https://the-history-farm.top/` per aprire direttamente la WebApp.

## Variabili `.env`
```
TELEGRAM_BOT_TOKEN=123:ABC
CATALOG_URL=https://thehistoryfarm.mysellauth.com/
VETRINA_SHIP_ITA_URL=https://thehistoryfarm.mysellauth.com/
VETRINA_SHIP_SPAGNA_URL=https://thehistoryfarm.mysellauth.com/
VETRINA_REVIEWS_URL=https://t.me/+reviews
TELEGRAM_CHANNEL_URL=https://t.me/+channel
TELEGRAM_CONTACT_URL=https://t.me/username
SIGNAL_CHANNEL_URL=https://signal.group/...
SIGNAL_CONTACT_URL=https://signal.me/#p/+39
INSTAGRAM_URL=https://instagram.com/...
```
Tutti i link sono facoltativi: se non impostati, il bot userà valori di default (la WebApp apre comunque `https://thehistoryfarm.mysellauth.com/`).

## Funzionalità
- `/start`, `/menu`: mostra menu inline con i bottoni (Potato, Telegram, Signal, Instagram, Vetrina).
- `/ping`: risponde `✅ Bot operativo` per health-check.
- Inline keyboard con callback per navigare fra i sotto-menu e pulsante WebApp.

## Deploy
Consulta [DEPLOY.md](DEPLOY.md) per il walkthrough completo (VPS, Nginx, HTTPS e DNS NameSilo).

Versione rapida:
1. Configura le stesse variabili `.env` nell'ambiente di produzione (VPS, Railway, ecc.).
2. Avvia il bot con `python -m bot.bot` e il backend con `python server.py` (o crea servizi systemd).
3. Se usi webhook invece del polling, configura il webhook con l'URL pubblico del bot; in questa repo il polling è la modalità predefinita.

## Note
- Il backend salva `data/products.json`: puoi editarlo a mano, ma è consigliato usare l'admin o l'endpoint `/api/products/reset` per tornare ai demo.
- Per inviare il logo con `/start`, lascia `logo.jpg` oppure aggiorna il percorso in `bot/bot.py`.
