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


def create_order(comment_id: str, provider: str, amount_som: int) -> str:
    order_id = secrets.token_hex(6)  # tasodifiy, taxmin qilib bo'lmaydi
    con = _db()
    try:
        con.execute(
            "INSERT INTO orders (order_id, comment_id, provider, amount_som, status, created_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            (order_id, comment_id, provider, amount_som, time.time()),
        )
        con.commit()
    finally:
        con.close()
    return order_id


def payme_link(order_id: str, amount_som: int) -> str:
    if not PAYME_MERCHANT_ID:
        raise PaymentNotConfigured("PAYME_MERCHANT_ID kiritilmagan")
    raw = f"m={PAYME_MERCHANT_ID};ac.{PAYME_ACCOUNT_FIELD}={order_id};a={amount_som * 100}"  # summa tiyinda
    return f"{PAYME_CHECKOUT_URL}/{base64.b64encode(raw.encode()).decode()}"


def click_link(order_id: str, amount_som: int) -> str:
    if not (CLICK_SERVICE_ID and CLICK_MERCHANT_ID):
        raise PaymentNotConfigured("CLICK_SERVICE_ID yoki CLICK_MERCHANT_ID kiritilmagan")
    return (
        "https://my.click.uz/services/pay"
        f"?service_id={CLICK_SERVICE_ID}&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount_som}&transaction_param={order_id}"
    )


def render(text: str, comment_id: str) -> str:
    """Matndagi {payme:SUMMA} va {click:SUMMA} belgilarini haqiqiy havolaga almashtiradi."""

    def replace(match: re.Match) -> str:
        provider, amount = match.group(1), int(match.group(2))
        make_link = payme_link if provider == "payme" else click_link
        make_link("check", amount)  # sozlanmagan bo'lsa, buyurtma yaratishdan oldin xato beradi
        order_id = create_order(comment_id, provider, amount)
        return make_link(order_id, amount)

    return TOKEN_RE.sub(replace, text)

