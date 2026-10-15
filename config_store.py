"""Bot sozlamalarini bazada saqlash (kalit so'zlar, biznes ma'lumoti, taqiqlangan so'zlar).

Hozircha bitta bloger ("default"). Keyin bir nechta bloger bo'lganda account_id
bo'yicha ajratiladi, jadval shunga tayyor.
"""
import json
import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "bot.db")

DEFAULTS = {
    "keywords": {
        "kurs": "Salom! Kurs narxi 300 000 so'm. To'lash uchun havola: https://example.com/pay/kurs",
        "narx": "Salom! Narxlar haqida batafsil: https://example.com/narxlar",
    },
    "business_info": (
        "- Kurs narxi: 300 000 so'm, 1 oy davom etadi.\n"
        "- Ish vaqti: har kuni 09:00-18:00.\n"
        "- To'lov usuli: Click yoki Payme."
    ),
    "blocklist": [],
}


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS settings ("
        "account_id TEXT, key TEXT, value TEXT, PRIMARY KEY (account_id, key))"
    )
    return con


def get_config(account_id: str = "default") -> dict:
    """Saqlangan sozlamalar; yo'q bo'lganlari uchun standart qiymatlar."""
    cfg = json.loads(json.dumps(DEFAULTS))  # nusxa
    con = _con()
    try:
        rows = con.execute(
            "SELECT key, value FROM settings WHERE account_id = ?", (account_id,)
        ).fetchall()
    finally:
        con.close()
    for key, value in rows:
        if key in cfg:
            cfg[key] = json.loads(value)
    return cfg


def save_config(cfg: dict, account_id: str = "default") -> None:
    con = _con()
    try:
        for key in DEFAULTS:
            if key in cfg:
                con.execute(
                    "INSERT OR REPLACE INTO settings (account_id, key, value) VALUES (?, ?, ?)",
                    (account_id, key, json.dumps(cfg[key], ensure_ascii=False)),
                )
        con.commit()
    finally:
        con.close()


# ---- Forma matnini ma'lumotga aylantirish va aksincha ----

def parse_keywords(text: str) -> dict:
    """Har qatorda: kalit so'z | javob matni"""
    result = {}
    for line in text.splitlines():
        if "|" not in line:
            continue
        key, reply = line.split("|", 1)
        key, reply = key.strip().lower(), reply.strip()
        if key and reply:
            result[key] = reply
    return result

