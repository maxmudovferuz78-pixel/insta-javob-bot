"""Instagram webhook serveri va bloger sozlamalar sahifasi.

Ishga tushirish:
    uvicorn server:app --reload --port 8000

Sahifalar:
    /webhook   Meta shu manzilga kommentlarni yuboradi
    /admin     sozlamalar va oxirgi kommentlar (ADMIN_PASSWORD kerak)
    /simulate  Meta'siz sinash (faqat DEBUG_SIMULATE=1 bo'lsa)
"""
import dataclasses
import html
import json
import os
import secrets
import time
from urllib.parse import parse_qs

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import config_store
import ig

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")

app = FastAPI(title="Instagram avtojavob bot")
security = HTTPBasic()


# ---------------- Meta webhook ----------------

@app.get("/webhook")
def verify_webhook(request: Request):
    """Meta webhook'ni ulaganingizda shu yerga bir marta tekshiruv so'rovi yuboradi."""
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and VERIFY_TOKEN and q.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(q.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="tekshiruv muvaffaqiyatsiz")


@app.post("/webhook")
async def receive_webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not ig.verify_signature(raw, request.headers.get("X-Hub-Signature-256"), ig.APP_SECRET):
        raise HTTPException(status_code=403, detail="imzo noto'g'ri")

    for comment in ig.extract_comments(json.loads(raw)):
        # Meta tez javob kutadi: og'ir ishni (AI, DM) orqa fonda bajaramiz
        background.add_task(ig.handle_comment, comment)
    return {"ok": True}


# ---------------- Admin sahifa ----------------

def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    password = os.getenv("ADMIN_PASSWORD", "")
    if not password:
        raise HTTPException(status_code=404)  # parol qo'yilmagan bo'lsa, sahifa o'chiq
    if not secrets.compare_digest(credentials.password.encode(), password.encode()):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})

