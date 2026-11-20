import json
import os
import secrets
import subprocess
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse

load_dotenv("/opt/ai-news-reader/.env", override=True)
TOKENS = [t.strip() for t in os.getenv("API_TOKEN", "").split(",") if t.strip()]
STORAGE = Path("/opt/ai-news-reader/storage")
APP_DIR = Path(__file__).parent
COOLDOWN = 600  # seconds between manual refreshes

app = FastAPI(title="AI Daily News")
state = {"running": False, "last_start": 0.0, "last_result": None}


def auth(x_api_token: str = Header(None), token: str = Query(None)):
    given = x_api_token or token or ""
    if not any(secrets.compare_digest(given, t) for t in TOKENS):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _run():
    try:
        p = subprocess.run(
            ["/opt/ai-news-reader/venv/bin/python", str(APP_DIR / "run_daily.py")],
            capture_output=True, text=True, timeout=900)
        state["last_result"] = "ok" if p.returncode == 0 else (p.stderr or p.stdout)[-300:]
    except Exception as e:
        state["last_result"] = str(e)
    finally:
        state["running"] = False


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/news/latest", dependencies=[Depends(auth)])
def news_latest():
    f = STORAGE / "latest.json"
    if not f.exists():
        raise HTTPException(404, "No edition yet")
    return json.loads(f.read_text(encoding="utf-8"))


@app.get("/api/edition/latest", dependencies=[Depends(auth)])
def edition_latest():
    f, pdf = STORAGE / "latest.json", STORAGE / "daily-news.pdf"
    if not f.exists() or not pdf.exists():
        raise HTTPException(404, "No edition yet")
    d = json.loads(f.read_text(encoding="utf-8"))
    return {"generated": d["generated"], "count": d["count"],
            "pdf_size": pdf.stat().st_size, "refreshing": state["running"]}


@app.get("/api/edition/pdf", dependencies=[Depends(auth)])
def edition_pdf():
    pdf = STORAGE / "daily-news.pdf"
    if not pdf.exists():
        raise HTTPException(404, "No edition yet")
    return FileResponse(pdf, media_type="application/pdf", filename="daily-news.pdf")


@app.post("/api/news/refresh", dependencies=[Depends(auth)])
def refresh():
    if state["running"]:
        return {"status": "already_running"}
    wait = COOLDOWN - (time.time() - state["last_start"])
    if wait > 0:
        raise HTTPException(429, f"Try again in {int(wait)}s")
    state.update(running=True, last_start=time.time(), last_result=None)
    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started"}


@app.get("/api/refresh/status", dependencies=[Depends(auth)])
def refresh_status():
    return {"running": state["running"], "last_result": state["last_result"]}


from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
def home():
    return (APP_DIR / "web.html").read_text(encoding="utf-8")


import re


@app.get("/api/img/{name}", dependencies=[Depends(auth)])
def get_image(name: str):
    if not re.fullmatch(r"[a-f0-9]{16}\.jpg", name):
        raise HTTPException(404, "Not found")
    f = STORAGE / "img" / name
    if not f.exists():
        raise HTTPException(404, "Not found")
    return FileResponse(f, media_type="image/jpeg", headers={"Cache-Control": "max-age=86400"})


import re


@app.get("/api/img/{name}", dependencies=[Depends(auth)])
def get_image(name: str):
    if not re.fullmatch(r"[a-f0-9]{16}\.jpg", name):
        raise HTTPException(404, "Not found")
    f = STORAGE / "img" / name
    if not f.exists():
        raise HTTPException(404, "Not found")
    return FileResponse(f, media_type="image/jpeg", headers={"Cache-Control": "max-age=86400"})
