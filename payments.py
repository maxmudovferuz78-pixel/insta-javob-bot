"""To'lov buyurtmalari va Payme/Click to'lov havolalarini yaratish.

Javob matnida (faqat kalit so'z shablonlarida) quyidagi belgilar ishlatiladi:
    {payme:300000}   -> 300 000 so'mlik Payme to'lov havolasi
    {click:300000}   -> 300 000 so'mlik Click to'lov havolasi
Har bir komment uchun alohida buyurtma yaratiladi.

DIQQAT: havola formatlari rasmiy hujjat bilan tekshirilmagan (uchinchi tomon
kutubxona hujjatlariga va umumiy bilimga tayangan). Merchant akkaunt olgach,
Payme va Click'ning o'z hujjatlari bilan solishtirib chiqing.
"""
import base64
import os
import re
import secrets
import sqlite3
import time

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "bot.db")

PAYME_MERCHANT_ID = os.getenv("PAYME_MERCHANT_ID", "")
PAYME_ACCOUNT_FIELD = os.getenv("PAYME_ACCOUNT_FIELD", "order_id")
PAYME_CHECKOUT_URL = os.getenv("PAYME_CHECKOUT_URL", "https://checkout.paycom.uz")

CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")

TOKEN_RE = re.compile(r"\{(payme|click):(\d+)\}")


class PaymentNotConfigured(Exception):
    pass


def _db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS orders ("
        "order_id TEXT PRIMARY KEY, comment_id TEXT, provider TEXT, "
        "amount_som INTEGER, status TEXT, created_at REAL, paid_at REAL)"
    )
    return con

