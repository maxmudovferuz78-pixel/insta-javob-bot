"""Instagram webhook serveri.

Ishga tushirish:
    uvicorn server:app --reload --port 8000

Meta'ga ko'rsatiladigan manzil: https://<sizning-domen>/webhook
Mahalliy sinash uchun .env ga DEBUG_SIMULATE=1 qo'shib, /simulate dan foydalaning.
"""
import dataclasses
import json
import os
import time

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

import ig

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")

app = FastAPI(title="Instagram avtojavob bot")


@app.get("/webhook")
def verify_webhook(request: Request):
    """Meta webhook'ni ulaganingizda shu yerga bir marta tekshiruv so'rovi yuboradi."""
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and VERIFY_TOKEN and q.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(q.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="tekshiruv muvaffaqiyatsiz")
