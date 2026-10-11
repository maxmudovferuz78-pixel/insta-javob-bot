"""Instagram bilan ishlash qismi: webhook'ni tekshirish, kommentni ajratib olish,
takroriy kommentlarni o'tkazib yuborish va private reply (DM) yuborish.

DRY_RUN=1 bo'lsa (standart), hech narsa haqiqatda yuborilmaydi, faqat ekranga yoziladi.
Haqiqiy yuborish uchun .env ga DRY_RUN=0 qo'yiladi (Meta ruxsati kelgandan keyin).
"""
import hashlib
import hmac
import os
import sqlite3
import time

import requests
from dotenv import load_dotenv

load_dotenv()

from bot_core import Decision, decide  # noqa: E402

APP_SECRET = os.getenv("META_APP_SECRET", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
GRAPH_HOST = os.getenv("GRAPH_HOST", "https://graph.instagram.com")
API_VERSION = os.getenv("GRAPH_API_VERSION", "v26.0")
DB_PATH = os.getenv("DB_PATH", "bot.db")
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"


def verify_signature(raw_body: bytes, header: str | None, secret: str) -> bool:
    """Meta har so'rovga X-Hub-Signature-256 imzosini qo'shadi. Soxta so'rovlarni shu bilan to'xtatamiz."""
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


