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


def _esc(value) -> str:
    return html.escape(str(value or ""))


ACTION_LABELS = {"reply": "javob berildi", "ignore": "jim turildi", "review": "ko'rib chiqing", "pending": "jarayonda"}


@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_page():
    cfg = config_store.get_config()
    rows = "".join(
        f"<tr class='{_esc(c['action'])}'><td>{_esc(c['text'])}</td>"
        f"<td>{_esc(ACTION_LABELS.get(c['action'], c['action']))}</td>"
        f"<td>{_esc(c['reason'])}</td><td>{_esc(c['reply'])}</td></tr>"
        for c in ig.recent_comments()
    ) or "<tr><td colspan='4'>Hali komment yo'q</td></tr>"
    return f"""<!doctype html><html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bot sozlamalari</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#222}}
textarea{{width:100%;font:inherit;padding:.5rem;box-sizing:border-box}}
button{{padding:.6rem 1.4rem;font-size:1rem;cursor:pointer}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}
td,th{{border:1px solid #ddd;padding:.4rem;text-align:left;vertical-align:top}}
tr.review{{background:#fff4d6}} tr.ignore{{color:#777}}
small{{color:#666}}
</style></head><body>
<h1>Bot sozlamalari</h1>
<form method="post" action="/admin">
<h3>Kalit so'zlar</h3>
<small>Har qatorda bittadan: <b>kalit so'z | javob matni</b>. Kommentda shu so'z bo'lsa, shu javob DM bo'lib boradi.</small>
<textarea name="keywords" rows="7">{_esc(config_store.format_keywords(cfg['keywords']))}</textarea>
<h3>Biznes ma'lumoti</h3>
<small>AI faqat shu ma'lumotga tayanib savollarga javob beradi: narx, manzil, ish vaqti, to'lov va hokazo.</small>
<textarea name="business_info" rows="8">{_esc(cfg['business_info'])}</textarea>
<h3>Taqiqlangan so'zlar</h3>
<small>Har qatorda bittadan. Kommentda shu so'z bo'lsa, bot javob bermaydi.</small>
<textarea name="blocklist" rows="4">{_esc(chr(10).join(cfg['blocklist']))}</textarea>
<p><button type="submit">Saqlash</button></p>
</form>
<h2>Oxirgi kommentlar</h2>
<table><tr><th>Komment</th><th>Qaror</th><th>Sabab</th><th>Yuborilgan javob</th></tr>{rows}</table>
</body></html>"""


@app.post("/admin", dependencies=[Depends(require_admin)])
async def save_admin(request: Request):
    # Boshqa saytdan yuborilgan so'rovlarni rad etamiz (CSRF'dan himoya)
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(status_code=403)
    form = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
    field = lambda name: form.get(name, [""])[0]  # noqa: E731
    config_store.save_config(
        {
            "keywords": config_store.parse_keywords(field("keywords")),
            "business_info": field("business_info").strip(),
            "blocklist": config_store.parse_lines(field("blocklist")),
        }
    )
    return RedirectResponse("/admin", status_code=303)


# ---------------- Meta'siz sinash ----------------

if os.getenv("DEBUG_SIMULATE") == "1":

    @app.post("/simulate")
    def simulate(body: dict):
        """{"text": "Narx qancha?"} yuboring."""
        comment = {"id": f"sim-{time.time()}", "text": body["text"], "from_id": "sim-user"}
        decision = ig.handle_comment(comment)
        return dataclasses.asdict(decision) if decision else {"skipped": True}