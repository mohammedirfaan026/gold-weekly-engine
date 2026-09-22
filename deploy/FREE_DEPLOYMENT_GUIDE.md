# 100% Free Production Deployment Guide ($0.00 / month forever)

This setup runs your Gold Weekly bias engine and minimal web interface completely free of cost with zero monthly fees.

---

## Architecture Overview

```
+-------------------------------------------------------------------+
|                        100% FREE STACK                            |
+-------------------------------------------------------------------+
| 1. Code & Pipeline : GitHub (mohammedirfaan026/gold-weekly-engine)|
| 2. Automation      : GitHub Actions (Free 2,000 mins/mo)          |
|                      - Runs model every Friday 21:30 UTC          |
|                      - Updates weekly predictions automatically   |
| 3. Cloud Web App   : Render.com / Koyeb (Free Tier)               |
|                      - Hosts minimal web interface with HTTPS     |
|                      - Auto-syncs on every GitHub update          |
| 4. Local Web App   : http://localhost:8787                        |
|                      - Instant local access with no login needed  |
+-------------------------------------------------------------------+
```

---

## Option A: 1-Click Free Cloud Web App (Render.com)

Render provides free hosting for Python web applications directly from GitHub:

1. Sign up for free at [render.com](https://render.com) (no credit card required).
2. Click **New +** → **Blueprint** (or **Web Service**).
3. Connect your GitHub repository: `mohammedirfaan026/gold-weekly-engine`.
4. Render will automatically read `render.yaml` and configure:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m web.app`
   - **Plan**: Free ($0/mo)
5. Click **Apply / Deploy**.
6. Within 2-3 minutes, you will receive a free public HTTPS URL:
   `https://gold-weekly-bias.onrender.com`

---

## Option B: Automated Free Friday Model Updates (GitHub Actions)

Your repository includes `.github/workflows/live_inference.yml`:

- **When it runs**: Automatically every Friday at 21:30 UTC (right after US market close).
- **What it does**:
  1. Executes the AI model inference.
  2. Updates `latest_brief.json` with the new weekly bias and explanation.
  3. Commits the changes back to your GitHub repository.
  4. Triggers Render to auto-refresh the live website.
- **Cost**: $0.00 (uses ~2 minutes per week out of GitHub's 2,000 free minutes/month).

### Optional: Adding Live Data API Keys to GitHub
If you want GitHub Actions to fetch real-time live FRED and news data:
1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**.
2. Add Repository Secrets:
   - `FRED_API_KEY`
   - `ALPHA_VANTAGE_API_KEY`
   - `FINNHUB_API_KEY`
   - `NEWS_API_KEY`
   - `TELEGRAM_BOT_TOKEN` (optional)
   - `TELEGRAM_CHAT_ID` (optional)

---

## Option C: Free Oracle Cloud ARM VM (Forever Free)

If you want a dedicated private 4-core, 24GB RAM Linux server forever:
- Follow `deploy/oracle_setup.sh`.
- Target: Oracle Cloud Always Free Ampere A1.
- Cost: $0.00 / month forever.

---

## Option D: Running Locally Anytime

To run on your current machine:
```bash
python -m web.app
```
Open **http://localhost:8787** in any browser.
