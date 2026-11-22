#!/usr/bin/env python3
"""
setup_webhook.py — TozaHavo Bot Webhook & Commands Setup Script

Reads TELEGRAM_BOT_TOKEN and VERCEL_URL from environment variables or a .env file,
registers the Telegram webhook, and sets bot commands.

Usage:
    python setup_webhook.py
    # or with inline env:
    VERCEL_URL=your-project.vercel.app python setup_webhook.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path


# ---------------------------------------------------------------------------
# Load .env file if present (simple parser, no external deps needed)
# ---------------------------------------------------------------------------
def load_dotenv(filepath: str = ".env") -> None:
    """Load key=value pairs from a .env file into os.environ (does not overwrite existing)."""
    env_path = Path(filepath)
    if not env_path.exists():
        return
    with env_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# ---------------------------------------------------------------------------
# Telegram API helpers
# ---------------------------------------------------------------------------
def telegram_request(token: str, method: str, payload: dict) -> dict:
    """Send a JSON POST request to the Telegram Bot API and return the parsed response."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        print(f"  ✗ HTTP {exc.code}: {body}")
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"  ✗ Network error: {exc.reason}")
        sys.exit(1)


def telegram_get(token: str, method: str) -> dict:
    """Send a GET request to the Telegram Bot API and return the parsed response."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        print(f"  ✗ HTTP {exc.code}: {body}")
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"  ✗ Network error: {exc.reason}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("  TozaHavo Bot — Webhook & Commands Setup")
    print("=" * 60)

    # 1. Load environment
    load_dotenv(".env")
    load_dotenv(".env.local")

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    raw_domain = os.environ.get("VERCEL_URL", "").strip()
    vercel_url = raw_domain.replace("https://", "").replace("http://", "").rstrip("/")

    if not token:
        print("\n✗ TELEGRAM_BOT_TOKEN is not set.")
        print("  Set it in your .env file or export it before running this script.")
        sys.exit(1)

    if not vercel_url:
        print("\n✗ VERCEL_URL is not set.")
        print("  Example: VERCEL_URL=your-project.vercel.app python setup_webhook.py")
        sys.exit(1)

    # Normalise URL — strip protocol prefix if user included it
    vercel_url = vercel_url.removeprefix("https://").removeprefix("http://").rstrip("/")
    webhook_url = f"https://{vercel_url}/api/webhook"

    print(f"\n  Token  : ...{token[-10:]}")
    print(f"  Webhook: {webhook_url}\n")

    # 2. Set webhook
    print("→ Setting webhook …")
    result = telegram_request(
        token,
        "setWebhook",
        {
            "url": webhook_url,
            "allowed_updates": [
                "message",
                "callback_query",
                "inline_query",
            ],
            "drop_pending_updates": True,
        },
    )
    if result.get("ok"):
        print(f"  ✓ {result.get('description', 'Webhook set successfully')}")
    else:
        print(f"  ✗ Failed: {result}")
        sys.exit(1)

    # 3. Set bot commands
    print("\n→ Registering bot commands …")
    commands = [
        {"command": "start",   "description": "Botni ishga tushirish"},
        {"command": "havo",    "description": "Joriy ob-havo ma'lumoti"},
        {"command": "sifat",   "description": "Havo sifati ma'lumoti"},
        {"command": "hudud",   "description": "Hududni o'zgartirish"},
        {"command": "yordam",  "description": "Yordam va qo'llanma"},
    ]
    result = telegram_request(token, "setMyCommands", {"commands": commands})
    if result.get("ok"):
        print("  ✓ Bot commands registered:")
        for cmd in commands:
            print(f"      /{cmd['command']:<10} — {cmd['description']}")
    else:
        print(f"  ✗ Failed: {result}")
        sys.exit(1)

    # 4. Get current bot info
    print("\n→ Verifying bot identity …")
    me = telegram_get(token, "getMe")
    if me.get("ok"):
        bot = me["result"]
        print(f"  ✓ Bot: @{bot.get('username')} (id={bot.get('id')})")
        print(f"  ✓ Name: {bot.get('first_name')}")
    else:
        print(f"  ✗ Could not fetch bot info: {me}")

    # 5. Confirm webhook info
    print("\n→ Fetching webhook info …")
    info = telegram_get(token, "getWebhookInfo")
    if info.get("ok"):
        wh = info["result"]
        print(f"  ✓ URL           : {wh.get('url')}")
        print(f"  ✓ Pending updates: {wh.get('pending_update_count', 0)}")
        if wh.get("last_error_message"):
            print(f"  ⚠ Last error    : {wh['last_error_message']}")
    else:
        print(f"  ✗ Could not fetch webhook info: {info}")

    print("\n" + "=" * 60)
    print("  Setup complete! Your bot is ready.")
    print(f"  Webhook → {webhook_url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
