"""Telegram bildirimi (opsiyonel). TELEGRAM_TOKEN ve TELEGRAM_CHAT_ID yoksa sessizce geçer."""
from __future__ import annotations

import os

import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}"


def enabled() -> bool:
    return bool(TOKEN and CHAT)


def send_text(text: str) -> None:
    if not enabled():
        return
    for i in range(0, len(text), 3900):
        requests.post(f"{API}/sendMessage", data={"chat_id": CHAT, "text": text[i : i + 3900],
                                                  "parse_mode": "HTML"}, timeout=20)


def send_photo(path: str, caption: str = "") -> None:
    if not enabled():
        return
    with open(path, "rb") as f:
        requests.post(f"{API}/sendPhoto", data={"chat_id": CHAT, "caption": caption[:1000],
                                                "parse_mode": "HTML"}, files={"photo": f}, timeout=30)
