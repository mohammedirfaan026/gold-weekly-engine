# VPS deploy — Gold Weekly live desk

Private stack:
1. Friday cron runs `run_weekly_live.py` (ingest → brief → Telegram)
2. Flask dashboard on port **8787** (password protected, read-only)

## 1. Server setup (Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
cd /opt
sudo git clone <your-repo-or-copy> gold
cd gold
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # fill API keys + Telegram + dashboard password
```

## 2. `.env` values for VPS

```env
# already have FRED / Finnhub / NewsAPI / Alpha Vantage

TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789

DASHBOARD_PASSWORD=choose-a-long-password
DASHBOARD_SECRET_KEY=random-long-string
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8787
DASHBOARD_PUBLIC_URL=https://your-domain-or-ip:8787
```

### Telegram bot
1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copy token → `TELEGRAM_BOT_TOKEN`
3. Message your bot once
4. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` → copy your `chat.id` → `TELEGRAM_CHAT_ID`

## 3. Cron (Friday 21:30 UTC ≈ after US close)

```bash
crontab -e
```

Paste (adjust path):

```cron
30 21 * * 5 cd /opt/gold && .venv/bin/python run_weekly_live.py >> /opt/gold/logs/weekly_live.log 2>&1
```

Or install example:

```bash
mkdir -p /opt/gold/logs
crontab deploy/crontab.example
```

## 4. Dashboard service

```bash
sudo cp deploy/gold-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gold-dashboard
sudo systemctl status gold-dashboard
```

Open `http://YOUR_VPS_IP:8787` → enter `DASHBOARD_PASSWORD`.

Put Nginx + HTTPS in front for production:

```nginx
server {
  listen 443 ssl;
  server_name gold.example.com;
  # ssl_certificate ...;
  location / {
    proxy_pass http://127.0.0.1:8787;
    proxy_set_header Host $host;
  }
}
```

## 5. Manual test

```bash
source .venv/bin/activate
python run_weekly_live.py --dry-run --skip-ingest   # build brief only
python run_weekly_live.py --skip-ingest              # brief + Telegram
python -m web.app                                   # dashboard
```

## Security
- Never expose dashboard without `DASHBOARD_PASSWORD`
- Firewall: allow 22 + 443 (or 8787 only from your IP)
- Do not commit `.env`
