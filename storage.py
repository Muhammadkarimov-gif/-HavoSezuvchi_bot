"""
api/storage.py — Lightweight storage for user region preferences & AQI history.

Supports:
  1. Upstash Redis (free tier) via REST API if UPSTASH_REDIS_REST_URL & UPSTASH_REDIS_REST_TOKEN are set.
  2. Local/Serverless JSON file (/tmp/users.json) as zero-config default.

Schema per user:
{
  "region": "tashkent",
  "last_aqi": 75,
  "last_aqi_time": "2026-11-22T09:00:00Z"
}
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional

STORAGE_PATH = "/tmp/users.json"
UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")


def _upstash_command(cmd: list) -> Optional[dict]:
    """Execute a command on Upstash Redis REST API using standard urllib."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return None
    try:
        url = f"{UPSTASH_URL.rstrip('/')}"
        req = urllib.request.Request(
            url,
            data=json.dumps(cmd).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result")
    except Exception:
        return None


def _load() -> dict:
    # Try Upstash first if configured
    if UPSTASH_URL and UPSTASH_TOKEN:
        res = _upstash_command(["GET", "tozahavo:users"])
        if res:
            try:
                return json.loads(res) if isinstance(res, str) else res
            except Exception:
                pass

    if not os.path.exists(STORAGE_PATH):
        return {}
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    # Try Upstash first if configured
    if UPSTASH_URL and UPSTASH_TOKEN:
        _upstash_command(["SET", "tozahavo:users", json.dumps(data, ensure_ascii=False)])

    try:
        with open(STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def get_user(user_id: int) -> Optional[dict]:
    """Return the stored record for user_id, or None if not found."""
    data = _load()
    return data.get(str(user_id))


def set_user_region(user_id: int, region_key: str) -> None:
    """Create or update the region preference for user_id."""
    data = _load()
    uid = str(user_id)
    record = data.get(uid, {})
    # Reset AQI if changing region so it won't trigger false comparison alerts
    if record.get("region") != region_key:
        record["last_aqi"] = None
        record["last_aqi_time"] = None
    record["region"] = region_key
    data[uid] = record
    _save(data)


def update_user_aqi(user_id: int, clean_pct: int) -> None:
    """Update the last known clean-air percentage for user_id."""
    data = _load()
    uid = str(user_id)
    record = data.get(uid, {})
    record["last_aqi"] = clean_pct
    record["last_aqi_time"] = datetime.now(timezone.utc).isoformat()
    data[uid] = record
    _save(data)


def get_all_users() -> dict:
    """Return the full users dict keyed by string user_id."""
    return _load()
