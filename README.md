# 🌬️ TozaHavo — Telegram Ob-havo & Havo Sifati Boti

> **Uzbek** | [English](#english)

---

## Uzbek

**TozaHavo** — O'zbekiston viloyatlari uchun real vaqt ob-havo ma'lumotlari va havo sifati (PM2.5/AQI) ko'rsatkichlarini taqdim etuvchi Telegram boti. Bot bepul Open-Meteo API dan foydalanadi, Vercel serverless platformasida ishlaydi va Telegram Mini App orqali chiroyli grafik interfeys taqdim etadi.

### ✨ Xususiyatlar (Uzbek)

- 🌡️ **Real vaqt ob-havo** — harorat, his qilish, namlik, shamol tezligi
- 🌿 **Havo sifati** — PM2.5, AQI, "Toza havo %" ko'rsatkichi
- 📍 **13 ta viloyat** — Toshkent, Navoiy, Samarqand, Buxoro, Farg'ona, Andijon, Namangan, Qashqadaryo, Surxondaryo, Jizzax, Sirdaryo, Xorazm, Qoraqalpog'iston
- 🤖 **AI yordamchi** — Pollinations.ai orqali havo haqida savollar
- 📲 **Mini App** — Telegram ichida interaktiv grafik interfeys
- 🔔 **Avtomatik bildirishnomalar** — havo sifati keskin o'zgarganda xabar
- 🌐 **O'zbek tilida** — barcha xabarlar o'zbek tilida

---

## English

**TozaHavo** ("Clean Air") is a Telegram bot that provides real-time weather and air quality data (PM2.5/AQI) for Uzbekistan's 13 regions. It uses the free Open-Meteo API, runs on Vercel serverless, and includes a Telegram Mini App with a beautiful animated UI.

### ✨ Features

- Real-time weather: temperature, feels-like, humidity, wind speed
- Air quality index: PM2.5, US AQI, clean-air percentage
- Coverage for all 13 Uzbekistan regions
- AI assistant powered by Pollinations.ai (free, no API key)
- Telegram Mini App with animated weather icons and SVG air quality gauge
- Automated AQI change notifications via Vercel Cron
- Fully serverless — zero ongoing server cost

---

## 📋 Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Vercel CLI | latest | `npm i -g vercel` |
| Git | any | [git-scm.com](https://git-scm.com) |

A **Telegram Bot Token** is required. Create one via [@BotFather](https://t.me/BotFather) with `/newbot`.

---

## 🚀 Deployment (Vercel)

### Step-by-step

```bash
# 1. Enter project directory
cd TozaHavo_bot

# 2. Install Vercel CLI (if not already installed)
npm i -g vercel

# 3. Log in to Vercel
vercel login

# 4. Add environment variables to Vercel
vercel env add TELEGRAM_BOT_TOKEN
# → paste your token when prompted, select all environments (Production, Preview, Development)

vercel env add VERCEL_URL
# → enter your planned project URL, e.g. tozahavo-bot.vercel.app
# → you can update this after the first deploy

vercel env add CRON_SECRET
# → generate a random string, e.g.: openssl rand -hex 32

# 5. Deploy to production
vercel --prod

# 6. After deployment completes, note your .vercel.app URL.
#    If VERCEL_URL was set incorrectly, update it:
vercel env rm VERCEL_URL production
vercel env add VERCEL_URL
# → enter the actual URL from step 5 output

# 7. Register the Telegram webhook and bot commands
#    Copy .env.example to .env and fill in your values:
cp .env.example .env
# Edit .env: set TELEGRAM_BOT_TOKEN and VERCEL_URL

python setup_webhook.py

# 8. Verify webhook registration
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

### Expected output from setup_webhook.py

```
============================================================
  TozaHavo Bot — Webhook & Commands Setup
============================================================

  Token  : ...VM_hbU4
  Webhook: https://your-project.vercel.app/api/webhook

→ Setting webhook …
  ✓ Webhook was set

→ Registering bot commands …
  ✓ Bot commands registered:
      /start      — Botni ishga tushirish
      /havo       — Joriy ob-havo ma'lumoti
      /sifat      — Havo sifati ma'lumoti
      /hudud      — Hududni o'zgartirish
      /yordam     — Yordam va qo'llanma

→ Verifying bot identity …
  ✓ Bot: @TozaHavoBot (id=123456789)

→ Fetching webhook info …
  ✓ URL           : https://your-project.vercel.app/api/webhook
  ✓ Pending updates: 0

============================================================
  Setup complete! Your bot is ready.
============================================================
```

---

## 💻 Local Development

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN, VERCEL_URL, CRON_SECRET

# 4. Run the development server
uvicorn api.index:app --reload --port 8000

# 5. Expose local server to the internet for Telegram webhooks (new terminal):
ngrok http 8000
# ngrok will show a URL like: https://abc123.ngrok.io

# 6. Register the webhook pointing to your ngrok URL:
VERCEL_URL=abc123.ngrok.io python setup_webhook.py

# 7. Open the bot in Telegram and test it!
```

> **Note:** Each time you restart ngrok you get a new URL and must re-run `setup_webhook.py`.

---

## 🏗️ Architecture Overview

```
TozaHavo_bot/
│
├── api/                        # Vercel serverless Python functions
│   ├── __init__.py             # Package init (empty)
│   ├── index.py                # FastAPI app — Vercel entry point, routes all requests
│   ├── bot.py                  # Telegram webhook handler (python-telegram-bot async)
│   ├── weather.py              # Open-Meteo weather + air quality data fetching
│   ├── storage.py              # User preferences (region) stored in /tmp/users.json
│   ├── ai_assistant.py         # Pollinations.ai free text AI integration
│   └── scheduler.py            # AQI change detection logic (called by Vercel Cron)
│
├── public/
│   └── miniapp/
│       └── index.html          # Telegram Mini App — single-file HTML/CSS/JS
│
├── .env.example                # Environment variable template
├── .env                        # Your local secrets (git-ignored)
├── .gitignore                  # Python + Node ignores
├── requirements.txt            # Python dependencies
├── setup_webhook.py            # Standalone webhook + commands registration script
├── vercel.json                 # Vercel build config + cron schedule
└── README.md                   # This file
```

### File Descriptions

| File | Purpose |
|------|---------|
| `api/index.py` | FastAPI application, Vercel serverless entry point. Mounts all HTTP routes: `/api/webhook` (POST), `/api/cron` (POST), `/api/weather` (GET), `/api/air-quality` (GET), `/miniapp` (GET). |
| `api/bot.py` | Processes incoming Telegram updates. Handles `/start`, `/havo`, `/sifat`, `/hudud`, `/yordam`, callback queries (region selection), and free-text AI queries. |
| `api/weather.py` | Fetches data from Open-Meteo forecast and air-quality APIs using `httpx`. Converts PM2.5 → US AQI → clean-air %. Returns structured dicts. |
| `api/storage.py` | Reads and writes `/tmp/users.json` to persist each user's chosen region. Falls back to `tashkent` if no preference is saved. |
| `api/ai_assistant.py` | POSTs natural-language weather questions to `https://text.pollinations.ai/` and formats the response as 4 bullet points. |
| `api/scheduler.py` | Iterates all stored users, fetches current AQI, compares with the last known value, and sends a Telegram push message if the change is ≥ 10 percentage points. |
| `public/miniapp/index.html` | Full Telegram Mini App. Uses `window.Telegram.WebApp`, Tailwind CDN, animated SVG weather icons, and an SVG circular AQI gauge. |
| `vercel.json` | Tells Vercel to build `api/index.py` with `@vercel/python` and run `/api/cron` every 3 hours. |
| `setup_webhook.py` | Standalone script. No third-party deps. Loads `.env`, calls `setWebhook` and `setMyCommands` on the Telegram API, prints confirmation. |
| `.env.example` | Template showing all required environment variables. Copy to `.env` and fill in. |

---

## ⚙️ Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `1234567890:ABC...` |
| `VERCEL_URL` | Your Vercel deployment domain (no `https://`) | `tozahavo.vercel.app` |
| `CRON_SECRET` | Random secret to protect the cron endpoint | `a1b2c3d4...` (32 hex chars) |

Generate a secure `CRON_SECRET`:
```bash
# Linux/macOS:
openssl rand -hex 32

# Python (any OS):
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🤖 Bot Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + region selection keyboard |
| `/havo` | Current weather for your saved region |
| `/sifat` | Current air quality for your saved region |
| `/hudud` | Change your region (inline keyboard) |
| `/yordam` | Help and usage guide |
| _(any text)_ | AI assistant answers your weather question |

---

## 🗺️ Supported Regions

| Key | Uzbek Name | Coordinates |
|-----|-----------|-------------|
| `tashkent` | Toshkent | 41.30°N, 69.24°E |
| `navoi` | Navoiy | 40.08°N, 65.38°E |
| `samarkand` | Samarqand | 39.65°N, 66.98°E |
| `bukhara` | Buxoro | 39.77°N, 64.43°E |
| `fergana` | Farg'ona | 40.39°N, 71.79°E |
| `andijan` | Andijon | 40.78°N, 72.34°E |
| `namangan` | Namangan | 41.00°N, 71.67°E |
| `kashkadarya` | Qashqadaryo | 38.86°N, 65.79°E |
| `surkhandarya` | Surxondaryo | 37.94°N, 67.57°E |
| `jizzakh` | Jizzax | 40.12°N, 67.84°E |
| `syrdarya` | Sirdaryo | 40.84°N, 68.66°E |
| `khorezm` | Xorazm | 41.55°N, 60.63°E |
| `karakalpakstan` | Qoraqalpog'iston | 42.46°N, 59.62°E |

---

## 🌐 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/webhook` | Telegram bot webhook receiver |
| `GET` | `/api/weather?region=tashkent` | Weather JSON for a region |
| `GET` | `/api/air-quality?region=tashkent` | Air quality JSON for a region |
| `POST` | `/api/cron` | Cron job — AQI change notifications |
| `GET` | `/miniapp` | Telegram Mini App HTML |

---

## 🛠️ Troubleshooting

### Webhook not receiving updates

1. Verify webhook is set:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
   ```
2. Check the `url` field matches your Vercel domain exactly.
3. Look at `last_error_message` in the response.
4. Re-run `python setup_webhook.py` after ensuring `VERCEL_URL` has no `https://` prefix.

### Bot responds with 500 errors

1. Check Vercel Function logs:
   ```bash
   vercel logs --prod
   ```
2. Make sure all three environment variables are set on Vercel:
   ```bash
   vercel env ls
   ```
3. Redeploy after adding missing variables:
   ```bash
   vercel --prod
   ```

### setup_webhook.py says "TELEGRAM_BOT_TOKEN is not set"

- Make sure `.env` exists in the project root (not `.env.example`).
- Or export the variable before running:
  ```bash
  # Windows PowerShell:
  $env:TELEGRAM_BOT_TOKEN="your-token"; python setup_webhook.py

  # Linux/macOS:
  TELEGRAM_BOT_TOKEN=your-token python setup_webhook.py
  ```

### Local uvicorn server not receiving webhooks

- Telegram only delivers webhooks to `https://` URLs.
- Use `ngrok http 8000` to get a public HTTPS tunnel, then re-run `setup_webhook.py` with the ngrok URL.
- Free ngrok URLs change on restart — re-run setup each time.

### AQI data not updating / cron not running

- Vercel Cron requires a **Pro plan** or the hobby plan free tier (limited to 1 cron per project on a daily schedule). Check your Vercel dashboard → Project → Cron Jobs.
- You can manually trigger the cron endpoint for testing:
  ```bash
  curl -X POST https://your-project.vercel.app/api/cron \
    -H "Authorization: Bearer <CRON_SECRET>"
  ```

### Mini App blank / not loading

- The Mini App is served at `https://<VERCEL_URL>/miniapp`.
- It calls `/api/weather?region=tashkent` — check the Vercel function logs for errors.
- Telegram Mini Apps require HTTPS; they will not work on `localhost` without ngrok.

---

## 📄 License

MIT — free to use, modify and distribute.

---

*Built with ❤️ for the people of Uzbekistan — breathing cleaner air, one update at a time.*
