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
