"""bot_core.py ni namunaviy kommentlar bilan avtomatik sinash.

Ishga tushirish:  python test_bot.py
Natijada qaysi komment kutilgandek, qaysi biri noto'g'ri chiqqani ko'rinadi.
"""
import time

from dotenv import load_dotenv

load_dotenv()

from bot_core import decide  # noqa: E402

# (komment, kutilgan harakat). Haqorat qatorlarini o'zing qo'shib ko'r.
CASES = [
    ("Ish vaqti qachon?", "reply"),
    ("Qanday to'lasam bo'ladi?", "reply"),
    ("Сколько стоит?", "reply"),
    ("Во сколько вы работаете?", "reply"),
    ("Manzil qayerda?", "review"),  # ma'lumotda yo'q, o'ylab topmasligi kerak
    ("zo'r 👏", "ignore"),
    ("🔥🔥🔥", "ignore"),
    ("Bizning kanalga kiring t.me/xxx", "ignore"),
    ("sen ahmoqsan, aldamchi", "ignore"),
    ("KURS", "reply"),  # kalit so'z
]
