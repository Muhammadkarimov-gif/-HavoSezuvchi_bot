"""
api/scheduler.py — Air quality change detection logic (called by Vercel Cron).

Every 3 hours the cron POSTs /api/cron. This module iterates all saved users,
fetches the current clean-air percentage for each user's region, compares with
the stored value, and sends a Telegram notification if the change is >= 10 pp.
"""

import os
import httpx
from api.storage import get_all_users, update_user_aqi
from api.weather import fetch_air_quality, REGIONS

BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8839466285:AAG2n6cdSioLZnrN491RVMOuyx2_VM_hbU4"
)
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHANGE_THRESHOLD = 10  # percentage points


async def _send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )


def _build_notification(region_name: str, old_pct: int, new_pct: int) -> str:
    if new_pct > old_pct:
        return (
            f"🌿 <b>{region_name}da havo tozaligi</b> {old_pct}% dan "
            f"{new_pct}% ga yaxshilandi! Havo bugun ancha toza."
        )
    else:
        return (
            f"😷 <b>{region_name}da havo tozaligi</b> {old_pct}% dan "
            f"{new_pct}% ga tushdi. Niqob tavsiya etiladi."
        )


async def run_cron() -> dict:
    """
    Main cron handler. Returns a summary dict suitable for JSON response.
    """
    users = get_all_users()
    if not users:
        return {"checked": 0, "notified": 0, "detail": "No users saved."}

    checked = 0
    notified = 0
    errors = []

    for uid_str, record in users.items():
        region_key = record.get("region")
        if not region_key or region_key not in REGIONS:
            continue

        aq = await fetch_air_quality(region_key)
        if aq is None:
            errors.append(f"uid={uid_str} fetch failed")
            continue

        new_pct = aq["clean_pct"]
        old_pct = record.get("last_aqi")  # may be None

        checked += 1

        if old_pct is not None:
            diff = abs(new_pct - old_pct)
            if diff >= CHANGE_THRESHOLD:
                try:
                    msg = _build_notification(aq["region_name"], old_pct, new_pct)
                    await _send_message(int(uid_str), msg)
                    notified += 1
                except Exception as e:
                    errors.append(f"uid={uid_str} send failed: {e}")

        # Always update stored AQI so next run compares against latest.
        update_user_aqi(int(uid_str), new_pct)

    return {
        "checked": checked,
        "notified": notified,
        "errors": errors,
    }
