"""
api/bot.py — Telegram webhook handler using python-telegram-bot v21 (async).

Handles:
  /start    — welcome + region keyboard + Mini App button
  /havo     — current weather for saved region
  /sifat    — air quality for saved region
  /hudud    — change region (inline keyboard)
  /yordam   — help message
  callback  — region selection from inline keyboard
  text      — AI assistant (4-bullet Uzbek answers)
"""

import os
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from api.weather import REGIONS, fetch_weather, fetch_air_quality, aqi_label
from api.storage import get_user, set_user_region, update_user_aqi
from api.ai_assistant import ask_ai

BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8839466285:AAG2n6cdSioLZnrN491RVMOuyx2_VM_hbU4"
)
_raw_domain = os.environ.get("VERCEL_URL", "tozahavo-bot.vercel.app").strip()
VERCEL_URL = _raw_domain.replace("https://", "").replace("http://", "").rstrip("/")
MINIAPP_URL = f"https://{VERCEL_URL}/miniapp"

# ---------------------------------------------------------------------------
# Keyboard builders
# ---------------------------------------------------------------------------

def _region_keyboard(callback_prefix: str = "region") -> InlineKeyboardMarkup:
    """Build a 2-column inline keyboard of all 13 Uzbekistan regions."""
    keys = list(REGIONS.keys())
    rows = []
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i : i + 2]:
            row.append(
                InlineKeyboardButton(
                    REGIONS[key]["name"], callback_data=f"{callback_prefix}:{key}"
                )
            )
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _miniapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🌐 Mini App ochish",
                    web_app=WebAppInfo(url=MINIAPP_URL),
                )
            ]
        ]
    )


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        "🌤️ <b>TozaHavo</b> — O'zbekiston bo'ylab havo va havo tozaligi boti.\n\n"
        "📍 Avval o'z hududingizni tanlang:"
    )
    keyboard = _region_keyboard(callback_prefix="region")
    # Append Mini App button as a last row
    rows = list(keyboard.inline_keyboard)
    rows.append(
        [InlineKeyboardButton("🌐 Mini App ochish", web_app=WebAppInfo(url=MINIAPP_URL))]
    )
    combined = InlineKeyboardMarkup(rows)
    await update.message.reply_html(text, reply_markup=combined)


async def cmd_havo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    record = get_user(user_id)
    if not record or not record.get("region"):
        await update.message.reply_html(
            "📍 Hududingiz tanlanmagan. Iltimos /hudud buyrug'i bilan hududni tanlang."
        )
        return

    region_key = record["region"]
    weather = await fetch_weather(region_key)
    if not weather:
        await update.message.reply_text("❌ Havo ma'lumotlarini olishda xatolik. Qayta urinib ko'ring.")
        return

    text = (
        f"{weather['emoji']} <b>{weather['region_name']} — Hozirgi ob-havo</b>\n\n"
        f"🌡️ Harorat: <b>{weather['temp']}°C</b> (his qilinishi: {weather['feels_like']}°C)\n"
        f"💧 Namlik: <b>{weather['humidity']}%</b>\n"
        f"💨 Shamol: <b>{weather['wind_speed']} km/h</b>\n"
        f"☀️ UV indeks: <b>{weather['uv_index']}</b>\n"
        f"📋 Holat: <b>{weather['description']}</b>"
    )
    await update.message.reply_html(text, reply_markup=_miniapp_keyboard())


async def cmd_sifat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    record = get_user(user_id)
    if not record or not record.get("region"):
        await update.message.reply_html(
            "📍 Hududingiz tanlanmagan. Iltimos /hudud buyrug'i bilan hududni tanlang."
        )
        return

    region_key = record["region"]
    aq = await fetch_air_quality(region_key)
    if not aq:
        await update.message.reply_text("❌ Havo sifati ma'lumotlarini olishda xatolik. Qayta urinib ko'ring.")
        return

    update_user_aqi(user_id, aq["clean_pct"])

    bars = _progress_bar(aq["clean_pct"])
    text = (
        f"🌬️ <b>{aq['region_name']} — Havo Sifati</b>\n\n"
        f"{aq['label_emoji']} Holat: <b>{aq['label']}</b>\n"
        f"🧹 Tozalik: <b>{aq['clean_pct']}%</b>\n"
        f"{bars}\n\n"
        f"📊 PM2.5: <b>{aq['pm25']} µg/m³</b>\n"
        f"📈 AQI: <b>{aq['aqi']}</b>"
    )
    await update.message.reply_html(text)


async def cmd_hudud(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "📍 <b>Hududni tanlang:</b>",
        reply_markup=_region_keyboard(callback_prefix="region"),
    )


async def cmd_yordam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "ℹ️ <b>TozaHavo Bot — Yordam</b>\n\n"
        "/start — Botni boshlash va hudud tanlash\n"
        "/havo — Hozirgi ob-havo ma'lumotlari\n"
        "/sifat — Havo tozaligi indeksi\n"
        "/hudud — Hududni o'zgartirish\n"
        "/yordam — Ushbu yordam xabari\n\n"
        "💬 Istalgan savol yozing — AI yordamchisi javob beradi!\n\n"
        "🔔 Bot har 3 soatda havo sifati o'zgarsa sizga xabar yuboradi."
    )
    await update.message.reply_html(text)


# ---------------------------------------------------------------------------
# Callback: region selection
# ---------------------------------------------------------------------------

async def callback_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data  # e.g. "region:tashkent"
    if ":" not in data:
        return
    _, region_key = data.split(":", 1)

    if region_key not in REGIONS:
        await query.edit_message_text("❌ Noma'lum hudud. Iltimos /hudud buyrug'ini qayta yuboring.")
        return

    user_id = query.from_user.id
    set_user_region(user_id, region_key)
    region_name = REGIONS[region_key]["name"]

    await query.edit_message_text(
        f"✅ Hudud saqlandi: <b>{region_name}</b>\n\n"
        "Hozirgi ob-havo uchun /havo, havo sifati uchun /sifat buyrug'ini yuboring.",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Text → AI assistant
# ---------------------------------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = update.message.text.strip()
    if not question:
        return

    # Show typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    answer = await ask_ai(question)
    await update.message.reply_html(
        f"🤖 <b>AI Yordamchi:</b>\n\n{answer}"
    )


# ---------------------------------------------------------------------------
# Helper: progress bar
# ---------------------------------------------------------------------------

def _progress_bar(pct: int, length: int = 10) -> str:
    filled = round(pct / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {pct}%"


# ---------------------------------------------------------------------------
# Application factory (re-used across requests)
# ---------------------------------------------------------------------------

_application: Application | None = None


def get_application() -> Application:
    global _application
    if _application is None:
        _application = (
            Application.builder()
            .token(BOT_TOKEN)
            .build()
        )
        _application.add_handler(CommandHandler("start", cmd_start))
        _application.add_handler(CommandHandler("havo", cmd_havo))
        _application.add_handler(CommandHandler("sifat", cmd_sifat))
        _application.add_handler(CommandHandler("hudud", cmd_hudud))
        _application.add_handler(CommandHandler("yordam", cmd_yordam))
        _application.add_handler(CallbackQueryHandler(callback_region, pattern=r"^region:"))
        _application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
        )
    return _application


async def process_update(update_data: dict) -> None:
    """Parse and dispatch a Telegram Update dict."""
    app = get_application()
    update = Update.de_json(update_data, app.bot)
    async with app:
        await app.process_update(update)
