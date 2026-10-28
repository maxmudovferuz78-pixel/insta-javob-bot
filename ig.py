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


def extract_comments(payload: dict) -> list[dict]:
    """Webhook ichidan kommentlarni ajratib oladi."""
    found = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue
            value = change.get("value", {})
            comment_id, text = value.get("id"), value.get("text")
            if not comment_id or not text:
                continue
            found.append(
                {
                    "id": comment_id,
                    "text": text,
                    "from_id": (value.get("from") or {}).get("id"),
                    "username": (value.get("from") or {}).get("username"),
                    "media_id": (value.get("media") or {}).get("id"),
                }
            )
    return found


def _db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS comments ("
        "comment_id TEXT PRIMARY KEY, text TEXT, action TEXT, reason TEXT, "
        "reply TEXT, created_at REAL)"
    )
    return con


def send_private_reply(comment_id: str, text: str) -> dict:
    """Kommentga DM orqali javob yuboradi (har bir komment uchun bitta, 7 kun ichida)."""
    if DRY_RUN:
        print(f"[DRY_RUN] komment {comment_id} ga DM: {text}")
        return {"dry_run": True}
    resp = requests.post(
        f"{GRAPH_HOST}/{API_VERSION}/{IG_USER_ID}/messages",
        headers={"Authorization": f"Bearer {IG_TOKEN}"},
        json={"recipient": {"comment_id": comment_id}, "message": {"text": text}},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def handle_comment(comment: dict) -> Decision | None:
    """Bitta kommentni to'liq qayta ishlaydi. Takroriy yoki o'zimizning komment bo'lsa None qaytaradi."""
    if comment.get("from_id") and comment["from_id"] == IG_USER_ID:
        return None  # o'z kommentimizga javob berib, cheksiz aylanishga tushmaymiz

    con = _db()
    try:
        # Meta ba'zan bir xil webhook'ni ikki marta yuboradi: ikkinchisini o'tkazib yuboramiz
        cur = con.execute(
            "INSERT OR IGNORE INTO comments (comment_id, text, action, created_at) VALUES (?, ?, 'pending', ?)",
            (comment["id"], comment["text"], time.time()),
        )
        con.commit()
        if cur.rowcount == 0:
            return None

        decision = decide(comment["text"])
        if decision.action == "reply":
            try:
                send_private_reply(comment["id"], decision.reply)
            except Exception as exc:
                decision = Decision("review", reason=f"yuborib bo'lmadi: {exc}")

        con.execute(
            "UPDATE comments SET action = ?, reason = ?, reply = ? WHERE comment_id = ?",
            (decision.action, decision.reason, decision.reply, comment["id"]),
        )
        con.commit()
        return decision
    finally:
        con.close()

