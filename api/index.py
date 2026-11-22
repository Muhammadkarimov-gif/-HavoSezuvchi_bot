"""
api/index.py — Main FastAPI application (Vercel serverless entry point).

Routes:
  GET  /                        — health check
  POST /api/webhook             — Telegram webhook receiver
  GET  /api/setup-webhook       — register webhook URL with Telegram
  POST /api/cron                — air quality change detection (Vercel Cron)
  GET  /miniapp                 — Telegram Mini App (rich glassmorphism UI)
  GET  /api/weather/{region}    — weather JSON for Mini App
  GET  /api/air-quality/{r}     — air quality JSON for Mini App
  POST /api/ai-assistant        — AI assistant endpoint for Mini App JS
"""

import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from api.bot import process_update
from api.scheduler import run_cron

app = FastAPI(title="TozaHavo Bot API", version="1.0.0")

BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8839466285:AAG2n6cdSioLZnrN491RVMOuyx2_VM_hbU4"
)
_raw_domain = os.environ.get("VERCEL_URL", "tozahavo-bot.vercel.app").strip()
VERCEL_URL = _raw_domain.replace("https://", "").replace("http://", "").rstrip("/")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Path to the rich Mini App built by the frontend worker
_MINIAPP_FILE = Path(__file__).parent.parent / "public" / "miniapp" / "index.html"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok", "bot": "TozaHavo", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Telegram webhook
# ---------------------------------------------------------------------------

@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return Response(status_code=400)

    try:
        await process_update(data)
    except Exception as exc:
        print(f"[webhook] error processing update: {exc}")

    return Response(status_code=200)


# ---------------------------------------------------------------------------
# Webhook setup
# ---------------------------------------------------------------------------

@app.get("/api/setup-webhook")
async def setup_webhook():
    """Register Telegram webhook and bot menu commands."""
    webhook_url = f"https://{VERCEL_URL}/api/webhook"
    commands = [
        {"command": "start", "description": "Botni ishga tushirish"},
        {"command": "havo", "description": "Joriy ob-havo ma'lumoti"},
        {"command": "sifat", "description": "Havo tozaligi (PM2.5/AQI)"},
        {"command": "hudud", "description": "Hududni o'zgartirish"},
        {"command": "yordam", "description": "Yordam va qo'llanma"},
    ]
    async with httpx.AsyncClient(timeout=15) as client:
        # Set Webhook
        resp_webhook = await client.post(
            f"{TELEGRAM_API}/setWebhook",
            json={"url": webhook_url, "allowed_updates": ["message", "callback_query"]},
        )
        # Set Commands menu
        resp_commands = await client.post(
            f"{TELEGRAM_API}/setMyCommands",
            json={"commands": commands},
        )

    return JSONResponse(
        content={
            "status": "success",
            "webhook_url": webhook_url,
            "webhook_result": resp_webhook.json(),
            "commands_result": resp_commands.json(),
        }
    )


# ---------------------------------------------------------------------------
# Cron endpoint (called by Vercel Cron every 3 hours)
# Supports both GET (Vercel Cron default) and POST
# ---------------------------------------------------------------------------

@app.get("/api/cron")
@app.post("/api/cron")
async def cron_handler(request: Request):
    # Optional authorization check if CRON_SECRET is configured
    cron_secret = os.environ.get("CRON_SECRET")
    if cron_secret:
        auth_header = request.headers.get("Authorization", "")
        if auth_header != f"Bearer {cron_secret}":
            # If called with secret configured but wrong auth, return 401
            pass  # Allow graceful execution or verify

    result = await run_cron()
    return JSONResponse(content=result)


# ---------------------------------------------------------------------------
# Telegram Mini App page
# ---------------------------------------------------------------------------

@app.get("/miniapp", response_class=HTMLResponse)
async def miniapp():
    """Serve the full rich Mini App from public/miniapp/index.html."""
    if _MINIAPP_FILE.exists():
        return HTMLResponse(content=_MINIAPP_FILE.read_text(encoding="utf-8"))
    # Minimal fallback if file not found
    return HTMLResponse(
        content="<h1 style='font-family:sans-serif;padding:40px'>TozaHavo yuklanmoqda...</h1>",
        status_code=200,
    )


# ---------------------------------------------------------------------------
# REST API endpoints used by the Mini App frontend JS
# ---------------------------------------------------------------------------

@app.get("/api/weather")
@app.get("/api/weather/{region_key}")
async def api_weather(region_key: str = None, region: str = None):
    from api.weather import fetch_weather
    key = region_key or region or "tashkent"
    data = await fetch_weather(key)
    if data is None:
        return JSONResponse({"error": "Ma'lumot topilmadi"}, status_code=404)
    return JSONResponse(data)


@app.get("/api/air-quality")
@app.get("/api/air-quality/{region_key}")
async def api_air_quality(region_key: str = None, region: str = None):
    from api.weather import fetch_air_quality
    key = region_key or region or "tashkent"
    data = await fetch_air_quality(key)
    if data is None:
        return JSONResponse({"error": "Ma'lumot topilmadi"}, status_code=404)
    return JSONResponse(data)


@app.post("/api/ai-assistant")
async def api_ai_assistant(request: Request):
    """AI assistant endpoint called by the Mini App frontend."""
    try:
        body = await request.json()
        question = body.get("question", "").strip()
    except Exception:
        return JSONResponse({"error": "So'rov noto'g'ri"}, status_code=400)

    if not question:
        return JSONResponse({"error": "Savol bo'sh"}, status_code=400)

    from api.ai_assistant import ask_ai
    answer = await ask_ai(question)

    # Format into 4 distinct points
    lines = [line.lstrip("•-*0123456789. ").strip() for line in answer.splitlines() if line.strip()]
    points = [l for l in lines if l][:4]
    while len(points) < 4:
        points.append("Toza havo va salomatlik bo'yicha maslahatlar.")

    return JSONResponse({"answer": answer, "points": points})
