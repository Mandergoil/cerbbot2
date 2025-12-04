# Deploy completo · The History Farm WebApp

Questa guida ti accompagna passo passo per portare online `server.py` (Flask) con dominio `the-history-farm.top`, reverse proxy Nginx + HTTPS e DNS NameSilo.

> **Prerequisiti**
> - VPS con Ubuntu 22.04+ (o equivalente) raggiungibile via IP pubblico.
> - Accesso SSH come utente con privilegi sudo.
> - Dominio registrato su NameSilo.

---

## 1. Preparazione VPS

Collegati via SSH e installa i pacchetti base:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
```

Clona la repo e configura l'ambiente virtuale:

```bash
cd /opt
sudo git clone https://github.com/Mandergoil/cerbbot2.git
sudo chown -R $USER:$USER cerbbot2
cd cerbbot2
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r bot/requirements.txt
```

Crea il file `.env` (per il bot) e verifica che `server.py` parta correttamente:

```bash
cp .env.example .env
# compila le variabili richieste, soprattutto TELEGRAM_BOT_TOKEN e CATALOG_URL
python server.py  # stoppa con CTRL+C dopo il test
```

### Systemd service (facoltativo ma consigliato)

Crea `/etc/systemd/system/historyfarm.service`:

```
[Unit]
Description=The History Farm Flask WebApp
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/cerbbot2
Environment="PATH=/opt/cerbbot2/.venv/bin"
ExecStart=/opt/cerbbot2/.venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Poi abilita e avvia:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now historyfarm.service
sudo systemctl status historyfarm.service
```

> **Nota:** se preferisci eseguire anche il bot Telegram sulla stessa VPS, crea un secondo servizio systemd (es. `historyfarm-bot.service`) che lanci `python -m bot.bot`.

---

## 2. Nginx + HTTPS (reverse proxy)

Crea un blocco server in `/etc/nginx/sites-available/historyfarm`:

```
server {
    listen 80;
    server_name the-history-farm.top www.the-history-farm.top;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Abilita il sito e riavvia Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/historyfarm /etc/nginx/sites-enabled/historyfarm
sudo nginx -t
sudo systemctl reload nginx
```

### Certificato Let's Encrypt

Esegui Certbot per ottenere SSL automatico:

```bash
sudo certbot --nginx -d the-history-farm.top -d www.the-history-farm.top
```

- Scegli l'opzione che forza il redirect HTTPS.
- Certbot imposta automaticamente il rinnovo.

Dopo il comando, verifica che `https://the-history-farm.top/` mostri la vetrina e `https://the-history-farm.top/admin` l'area admin.

---

## 3. DNS NameSilo

1. Accedi al [Domain Manager NameSilo](https://www.namesilo.com/account_domains.php).
2. Clicca sul dominio `the-history-farm.top` → **DNS Records**.
3. Aggiungi/aggiorna:
   - **A Record**: Host `@`, Value `IP_della_VPS`, TTL `3600`.
   - **A Record**: Host `www`, Value `IP_della_VPS`, TTL `3600`.
   - (opzionale) **AAAA** se la VPS ha IPv6.
4. Salva e attendi la propagazione (da 5 minuti a 1 ora).

> Puoi usare `nslookup the-history-farm.top` o `dig the-history-farm.top` per verificare che il record punti all'IP corretto.

---

## 4. Collegamento con il bot Telegram

- Nel file `.env` assicurati che `CATALOG_URL=https://the-history-farm.top/`.
- Riavvia il servizio del bot (o il processo manuale).
- Dal bot, premi il bottone WebApp per verificare che apra il nuovo dominio.

---

## 5. Checklist finale

- [ ] `https://the-history-farm.top/` carica la vetrina con media.
- [ ] `https://the-history-farm.top/admin` raggiungibile e protetto da HTTPS.
- [ ] Admin salva prodotti senza errori e la vetrina mostra gli aggiornamenti.
- [ ] Certbot ha generato certificati validi (`sudo certbot certificates`).
- [ ] NameSilo punta correttamente all'IP della VPS.
- [ ] Il bot Telegram usa `CATALOG_URL` aggiornato.

Se vuoi automatizzare ulteriormente (CI/CD, backup `data/products.json`, ecc.) fammelo sapere e preparo altri script.
