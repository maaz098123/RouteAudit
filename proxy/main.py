"""
RouteAudit - Day 2: passthrough proxy that logs every call to SQLite.

Your app calls THIS server instead of the router.
This server forwards the request, returns the answer unchanged,
and saves the details of every call to routeaudit.db.

Run it:   uvicorn proxy.main:app --reload --port 8001
          (run from inside the routeaudit/ folder)
"""

import hashlib
import json
import os
import time
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from proxy.db import init_db, save_call

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

load_dotenv()

ROUTER_BASE_URL = os.getenv("ROUTER_BASE_URL", "https://openrouter.ai/api/v1")
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")
ROUTER_NAME = os.getenv("ROUTER_NAME", "openrouter")

if not ROUTER_API_KEY:
    raise RuntimeError("ROUTER_API_KEY is missing. Put it in your .env file.")

app = FastAPI(title="RouteAudit proxy")
init_db()  # creates routeaudit.db and the calls table on first run


@app.get("/health")
async def health():
    return {"status": "ok"}


def make_prompt_hash(messages) -> str:
    """Short fingerprint of the conversation. Same question twice -> same hash -> retry."""
    text = json.dumps(messages, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# The passthrough endpoint
# ---------------------------------------------------------------------------

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()

    # Written by Maaz: headers for the router.
    headers = {
        "Authorization": f"Bearer {ROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Written by Maaz: forward the request, timed.
    url = ROUTER_BASE_URL + "/chat/completions"
    start = time.time()
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, headers=headers, timeout=60)
    duration_ms = int((time.time() - start) * 1000)

    data = response.json()
    usage = data.get("usage") or {}

    # Only failed calls have an "error" section.
    error_message = None
    if response.status_code != 200:
        error_message = (data.get("error") or {}).get("message")

    # The app can send a session ID in a header so we can group conversation turns.
    session_id = request.headers.get("x-session-id")

    # Save the call (column design by Maaz).
    save_call({
        "timestamp": datetime.now().isoformat(),
        "router": ROUTER_NAME,
        "session_id": session_id,
        "requested_model": body.get("model"),
        "model_used": data.get("model"),
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "cost_usd": usage.get("cost"),
        "prompt_hash": make_prompt_hash(body.get("messages")),
        "request_body": json.dumps(body),
        "response_body": json.dumps(data),
        "error_message": error_message,
    })

    # Send the router's answer back to the app, unchanged.
    return JSONResponse(content=data, status_code=response.status_code)