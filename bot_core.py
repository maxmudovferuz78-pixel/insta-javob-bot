"""Instagram avtojavob bot: asosiy miya.

Instagram'siz, terminalda sinash uchun. Keyin faqat kirish (komment keladi)
va chiqish (javob yuboriladi) qismlarini Instagram API bilan almashtiramiz.

Ishga tushirish:
    pip install google-genai
    export GEMINI_API_KEY="sizning_kalitingiz"   # Windows: set GEMINI_API_KEY=...
    python bot_core.py
"""
import json
import os
import re
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# ---------- Sozlamalar: bloger shularni to'ldiradi ----------
KEYWORDS = {
    "kurs": "Salom! Kurs narxi 300 000 so'm. To'lash uchun havola: https://example.com/pay/kurs",
    "narx": "Salom! Narxlar haqida batafsil: https://example.com/narxlar",
}

BUSINESS_INFO = """
- Kurs narxi: 300 000 so'm, 1 oy davom etadi.
- Ish vaqti: har kuni 09:00-18:00.
- To'lov usuli: Click yoki Payme.
"""

# Aniq haqorat so'zlarini o'zing shu yerga qo'sh (kichik harflarda, lotin).
BLOCKLIST = []

