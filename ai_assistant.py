"""
api/ai_assistant.py — Free AI integration.
Supports:
  1. Google Gemini API free tier (if GEMINI_API_KEY is set in env)
  2. Pollinations.ai free API (default, 100% free, no key required)

Always returns exactly 4 distinct, clear bullet answer points in Uzbek.
"""

import os
import re
import httpx

POLLINATIONS_URL = "https://text.pollinations.ai/"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = (
    "Sen TozaHavo Telegram botining aqlli AI yordamchisisan. "
    "Foydalanuvchi qanday savol bersa ham, javobing faqat O'zbek tilida (lotin alifbosida) bo'lsin. "
    "QAT'IY QOIDA: Har doim aniq 4 ta alohida punkt (bullet point) shaklida javob ber. "
    "Har bir punkt yangi qatordan '1. ', '2. ', '3. ', '4. ' yoki '• ' bilan boshlansin. "
    "Javoblar qisqa, aniq, lo'nda va foydali bo'lsin."
)


def _format_into_four_points(raw_text: str) -> str:
    """Ensure the output is strictly 4 clear bullet points."""
    lines = [
        re.sub(r"^[-•*0-9.)\s]+", "", line).strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]
    # Filter out empty or too short lines
    lines = [l for l in lines if len(l) > 3]

    if len(lines) >= 4:
        points = lines[:4]
    elif len(lines) > 0:
        points = lines
        while len(points) < 4:
            points.append("Qo'shimcha ma'lumot olish uchun savolingizni aniqlashtiring.")
    else:
        return _fallback()

    return "\n".join([f"• {p}" for p in points])


async def _ask_gemini(user_question: str) -> str:
    """Call Google Gemini API free tier if GEMINI_API_KEY is configured."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\nFoydalanuvchi savoli: {user_question}"}
                ]
            }
        ],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _format_into_four_points(text)


async def _ask_pollinations(user_question: str) -> str:
    """Call Pollinations free text API (no API key needed)."""
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_question},
        ],
        "model": "openai",
        "private": True,
    }
    async with httpx.AsyncClient(timeout=25) as client:
        resp = await client.post(POLLINATIONS_URL, json=payload)
        resp.raise_for_status()
        return _format_into_four_points(resp.text)


async def ask_ai(user_question: str) -> str:
    """
    Send question to Gemini (if key provided) or Pollinations (free zero-config).
    Guarantees 4 clear answer points in Uzbek.
    """
    if GEMINI_API_KEY:
        try:
            return await _ask_gemini(user_question)
        except Exception:
            pass  # Fallback to Pollinations

    try:
        return await _ask_pollinations(user_question)
    except Exception:
        return _fallback()


def _fallback() -> str:
    return (
        "• Toza havo — salomatlik va uzoq umr ko'rish garovi.\n"
        "• PM2.5 miqdori yuqori bo'lganda tibbiy niqob taqish tavsiya etiladi.\n"
        "• Hududingizdagi joriy ob-havo uchun /havo, havo tozaligi uchun /sifat buyrug'ini yuboring.\n"
        "• To'liq ma'lumot va interaktiv xaritani ko'rish uchun Mini App'ni oching."
    )
