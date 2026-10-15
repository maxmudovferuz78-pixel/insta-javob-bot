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


